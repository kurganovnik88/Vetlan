from pybit.unified_trading import HTTP
import os
from dotenv import load_dotenv

load_dotenv()


class BybitClient:
    def __init__(self, config):
        self.testnet = config["environment"] != "mainnet"


        # Основной HTTP-клиент pybit
        self.client = HTTP(
            testnet=self.testnet,
            api_key=config["api_key"],
            api_secret=config["api_secret"],
            recv_window=5000
        )

        # Отключаем проверку SSL (ТОЛЬКО в учебных целях)
        try:
            self.client._session.verify = False
        except Exception:
            pass

    def get_klines(self, symbol, interval="1", limit=200):
        try:
            resp = self.client.get_kline(
                category="linear",
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            return resp.get("result", {}).get("list", [])
        except Exception as e:
            raise RuntimeError(f"Ошибка загрузки свечей {symbol}: {e}")

    def place_market_order(self, symbol, side, qty):
        try:
            return self.client.place_order(
                category="linear",
                symbol=symbol,
                side=side,
                orderType="Market",
                qty=str(qty),
                timeInForce="IOC",
            )
        except Exception as e:
            raise RuntimeError(f"Ошибка отправки ордера: {e}")

    def get_positions(self, symbol):
        resp = self.client.get_positions(
            category="linear", symbol=symbol
        )
        return resp.get("result", {}).get("list", [])

    def get_balance(self):
        return self.client.get_wallet_balance(accountType="UNIFIED")
