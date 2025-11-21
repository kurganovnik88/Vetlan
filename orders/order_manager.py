import math


class OrderManager:
    def __init__(self, client, cfg, notifier=None):
        self.client = client
        self.cfg = cfg
        self.notifier = notifier

        self.risk_pct = cfg["risk_pct"] / 100.0  # из процентов в доли
        self.position_cache = {}
        self.enable_tp_sl = cfg.get("enable_tp_sl", True)
        self.min_order_usdt = cfg.get("min_order_usdt", 5)
        self.max_position_pct = cfg.get("max_position_pct", 10) / 100.0  # из процентов в доли

    # ---------------------------
    # Расчёт размера позиции
    # ---------------------------
    def calc_qty(self, entry, sl):
        balance = self._get_usdt_balance()
        if balance <= 0:
            raise RuntimeError("Не найден баланс для расчёта позиции")

        risk_usdt = balance * self.risk_pct
        sl_dist = abs(entry - sl)

        if sl_dist <= 0:
            return 0

        qty = risk_usdt / sl_dist
        if qty <= 0:
            return 0

        # Округляем до целого числа
        qty = math.floor(qty)
        if qty < 1:
            return 0

        # Проверка минимального размера ордера
        if entry * qty < self.min_order_usdt:
            qty = math.ceil(self.min_order_usdt / entry)

        # Ограничение максимального размера позиции
        max_position_usdt = balance * self.max_position_pct
        max_qty = max_position_usdt / entry
        if qty > max_qty:
            qty = math.floor(max_qty)
            if qty < 1:
                return 0

        return float(qty)

    # ---------------------------
    # Получение баланса
    # ---------------------------
    def _get_usdt_balance(self):
        try:
            resp = self.client.get_wallet_balance(accountType="UNIFIED")
            wallets = resp.get("result", {}).get("list", [])
            if not wallets:
                return 0

            for c in wallets[0].get("coin", []):
                if c["coin"] == "USDT":
                    return float(c["walletBalance"])
            return 0

        except Exception:
            return 0

    def get_usdt_balance(self):
        return self._get_usdt_balance()

    def refresh_position(self, symbol):
        previous_state = self.position_cache.get(symbol)

        try:
            resp = self.client.get_positions(
                category="linear",
                symbol=symbol
            )
        except Exception:
            return previous_state

        pos_list = resp.get("result", {}).get("list", [])
        open_pos = None
        for p in pos_list:
            if float(p.get("size", 0)) > 0:
                open_pos = p
                break

        if open_pos:
            self.position_cache[symbol] = open_pos
            return open_pos

        if previous_state and previous_state.get("pending"):
            return previous_state

        self.position_cache[symbol] = None
        return None

    def list_open_positions(self, symbols):
        positions = []
        for symbol in symbols:
            pos = self.refresh_position(symbol)
            if not pos:
                continue

            if pos.get("pending"):
                continue

            positions.append(
                {
                    "symbol": symbol,
                    "size": float(pos.get("size", 0)),
                    "entryPrice": float(pos.get("entryPrice", 0)),
                }
            )
        return positions

    # ---------------------------
    # Проверка открытых позиций
    # ---------------------------
    def has_open_position(self, symbol, use_cache=False):
        if use_cache and symbol in self.position_cache:
            return self.position_cache[symbol] is not None

        pos = self.refresh_position(symbol)
        return pos is not None



    # ---------------------------
    # Основной вход в позицию
    # ---------------------------
    def enter_position(self, symbol, signal, entry, tp, sl):
        """
        signal: "long" или "short"
        """
        if self.has_open_position(symbol):
            return False

        qty = self.calc_qty(entry, sl)
        if qty <= 0:
            return False

        side = "Buy" if signal == "long" else "Sell"

        order_kwargs = {}
        if self.enable_tp_sl:
            order_kwargs = {
                "takeProfit": str(tp),
                "stopLoss": str(sl),
                "tpTriggerBy": "LastPrice",
                "slTriggerBy": "LastPrice",
            }

        try:
            resp = self.client.place_order(
                category="linear",
                symbol=symbol,
                side=side,
                orderType="Market",
                qty=str(qty),
                **order_kwargs,
            )
        except Exception:
            self.position_cache.pop(symbol, None)
            raise

        # блокируем повторный вход до прояснения статуса
        self.position_cache[symbol] = {"pending": True, "symbol": symbol}

        if self.notifier:
            self.notifier.send(
                f"📌 {symbol}\n"
                f"Вход: {signal.upper()}\n"
                f"Цена: {entry}\n"
                f"TP: {tp}\n"
                f"SL: {sl}\n"
                f"Объём: {qty}"
            )

        return True

    # ---------------------------
    # Установка TP и SL
    # ---------------------------
    def set_tp_sl(self, symbol, signal, qty, tp, sl):

        side = "Buy" if signal == "long" else "Sell"
        opposite = "Sell" if signal == "long" else "Buy"

        # TP
        self.client.place_order(
            category="linear",
            symbol=symbol,
            side=opposite,
            orderType="Limit",
            qty=str(qty),
            price=str(tp),
            timeInForce="GTC",
            reduceOnly=True,
        )

        # SL (не используется в текущей версии, оставлено для совместимости)
