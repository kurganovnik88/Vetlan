import logging
from exchange.bybit_client import BybitClient
from config.bybit_config import BYBIT_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vetlan_main")


def main():
    logger.info("=== VetlanBot: Проверка подключения к Bybit ===")

    client = BybitClient(BYBIT_CONFIG)
    test_symbol = BYBIT_CONFIG["coins"][0]
    interval = BYBIT_CONFIG["interval"]

    # --- Проверка ключей и подключения ---
    try:
        logger.info(f"Подключение к Bybit ({BYBIT_CONFIG['environment'].upper()}) успешно.")
        logger.info(f"URL: {'https://api.bybit.com' if BYBIT_CONFIG['environment']=='mainnet' else 'https://api-testnet.bybit.com'}")
    except Exception as e:
        logger.error(f"Ошибка подключения: {e}")
        return

    # --- Проверка баланса ---
    try:
        balance = client.get_balance()
        list_data = balance.get("result", {}).get("list", [])
        usdt = 0

        if list_data:
            for c in list_data[0].get("coin", []):
                if c["coin"] == "USDT":
                    usdt = float(c["walletBalance"])

        logger.info(f"Баланс найден: {usdt:.2f} USDT")
    except Exception as e:
        logger.error(f"Ошибка при получении баланса: {e}")

    # --- Проверка свечей ---
    try:
        resp = client.client.get_kline(
            category="linear",
            symbol=test_symbol,
            interval=interval,
            limit=5
        )
        klines = resp.get("result", {}).get("list", [])

        if klines:
            logger.info(f"Получены свечи по {test_symbol}: {len(klines)} шт.")
        else:
            logger.warning(f"Свечи по {test_symbol} не получены.")

    except Exception as e:
        logger.error(f"Ошибка при получении свечей: {e}")

    logger.info("Бот готов. Для запуска стратегии: python run_strategy.py")


if __name__ == "__main__":
    main()
