import time
import logging
from exchange.bybit_client import BybitClient
from strategy.strategy import Strategy
from orders.order_manager import OrderManager
from utils.notifier import TelegramNotifier
from utils.stats_logger import StatsLogger
from config.bybit_config import BYBIT_CONFIG


logger = logging.getLogger("vetlan_strategy")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    logger.addHandler(handler)


def format_positions_report(positions):
    if not positions:
        return "Открытых позиций нет."

    lines = ["Открытые позиции:"]
    for pos in positions:
        lines.append(
            "- {symbol}: размер {size:.4f}, вход {entry:.4f}".format(
                symbol=pos["symbol"],
                size=pos["size"],
                entry=pos["entryPrice"],
            )
        )
    return "\n".join(lines)


def run_strategy(poll_interval: int = 30):
    """
    Запускает основной цикл проверки сигналов по списку монет.
    """
    client = BybitClient(BYBIT_CONFIG)

    notifier = TelegramNotifier(
        BYBIT_CONFIG.get("telegram_token"),
        BYBIT_CONFIG.get("telegram_chat_id"),
    )

    orders = OrderManager(
        client=client.client,
        cfg=BYBIT_CONFIG,
        notifier=notifier,
    )

    strategy = Strategy(
        client=client.client,
        orders=orders,
        settings=BYBIT_CONFIG,
    )

    stats_logger = StatsLogger()

    coins = BYBIT_CONFIG["coins"]
    logger.info("Запущена стратегия. Монеты: %s", ", ".join(coins))

    tracked_positions = {}
    initial_positions = orders.list_open_positions(coins)
    for pos in initial_positions:
        tracked_positions[pos["symbol"]] = pos

    if notifier:
        balance = orders.get_usdt_balance()
        notifier.send(
            "🤖 Бот запущен\n"
            f"Баланс: {balance:.2f} USDT\n"
            f"{format_positions_report(initial_positions)}"
        )

    try:
        while True:
            for symbol in coins:
                prev_position = tracked_positions.get(symbol)
                current_position = orders.refresh_position(symbol)

                if current_position:
                    if current_position.get("pending"):
                        tracked_positions[symbol] = {"pending": True}
                        continue

                    tracked_positions[symbol] = {
                        "symbol": symbol,
                        "size": float(current_position.get("size", 0)),
                        "entryPrice": float(current_position.get("entryPrice", 0)),
                    }
                elif prev_position:
                    if prev_position.get("pending"):
                        tracked_positions.pop(symbol, None)
                    else:
                        # Позиция закрыта - логируем
                        entry_price = prev_position.get("entryPrice", 0)
                        size = prev_position.get("size", 0)
                        
                        # Получаем текущую цену как цену выхода
                        try:
                            klines_resp = client.client.get_kline(
                                category="linear",
                                symbol=symbol,
                                interval="1",
                                limit=1
                            )
                            if klines_resp.get("retCode") == 0:
                                klines = klines_resp.get("result", {}).get("list", [])
                                if klines:
                                    exit_price = float(klines[0][4])  # close price
                                    
                                    # Определяем направление позиции (нужно получить из истории или использовать сигнал)
                                    # Для упрощения используем разницу цен
                                    direction = "long" if exit_price > entry_price else "short"
                                    
                                    # Расчёт PnL
                                    if direction == "long":
                                        pnl = (exit_price - entry_price) * size
                                    else:
                                        pnl = (entry_price - exit_price) * size
                                    
                                    roi = (pnl / (entry_price * size)) * 100 if entry_price * size > 0 else 0
                                    
                                    stats_logger.log_trade(
                                        symbol=symbol,
                                        direction=direction,
                                        entry=entry_price,
                                        tp=0,  # Не знаем TP/SL при закрытии
                                        sl=0,
                                        exit_price=exit_price,
                                        pnl=pnl,
                                        roi=roi,
                                    )
                        except Exception as e:
                            logger.warning("[%s] Ошибка при логировании закрытия: %s", symbol, e)
                        
                        tracked_positions.pop(symbol, None)
                        if notifier:
                            notifier.send(
                                "📤 Позиция закрыта\n"
                                f"Символ: {symbol}\n"
                                f"Размер: {size:.4f}\n"
                                f"Цена входа: {entry_price:.4f}"
                            )

                name, signal, decision = strategy.analyze_symbol(symbol)
                decision = decision or {}

                message = decision.get("message", "Нет комментария")
                indicators = decision.get("indicators", [])
                details = " | ".join(indicators) if indicators else ""

                log_line = f"[{symbol}] {message}"
                if details:
                    log_line += f" | {details}"
                logger.info(log_line)

                if not signal:
                    continue

                log_line = f"[{symbol}] СИГНАЛ: {signal.upper()} — {message}"
                if details:
                    log_line += f" | {details}"
                logger.info(log_line)

                entry = decision.get("entry")
                tp = decision.get("tp")
                sl = decision.get("sl")

                if entry is None or tp is None or sl is None:
                    logger.warning(
                        "[%s] Сигнал без уровней (entry/tp/sl). Пропуск.",
                        symbol,
                    )
                    continue

                success = False
                try:
                    success = orders.enter_position(
                        symbol=symbol,
                        signal=signal,
                        entry=entry,
                        tp=tp,
                        sl=sl,
                    )
                except Exception as exc:
                    logger.warning("[%s] Ошибка открытия позиции: %s", symbol, exc)
                    continue

                if success:
                    new_position = orders.refresh_position(symbol)
                    if new_position and not new_position.get("pending"):
                        tracked_positions[symbol] = {
                            "symbol": symbol,
                            "size": float(new_position.get("size", 0)),
                            "entryPrice": float(new_position.get("entryPrice", 0)),
                        }
                        
                        # Логируем открытие позиции
                        stats_logger.log_trade(
                            symbol=symbol,
                            direction=signal,
                            entry=entry,
                            tp=tp,
                            sl=sl,
                        )

                    if notifier:
                        notifier.send(
                            f"🟢 Открыт ордер\n"
                            f"{log_line}\n"
                            f"Entry: {entry:.6f}\nTP: {tp:.6f}\nSL: {sl:.6f}"
                        )
                else:
                    logger.warning("[%s] Не удалось открыть позицию", symbol)

            time.sleep(max(1, poll_interval))
    except KeyboardInterrupt:
        logger.info("Остановка бота по запросу пользователя.")
    finally:
        if notifier:
            notifier.send("⏹️ Бот остановлен.")


if __name__ == "__main__":
    run_strategy()
