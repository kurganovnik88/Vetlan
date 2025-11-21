import csv
import os
from datetime import datetime

class TradeLogger:
    def __init__(self, file_path="logs/trades.csv"):
        self.file_path = file_path
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        if not os.path.exists(file_path):
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Дата открытия", "Символ", "Направление", "Цена входа", "TP", "SL",
                    "Цена выхода", "PnL (USDT)", "ROI (%)", "Длительность (мин)"
                ])

    def log_trade(self, data: dict):
        """Записывает сделку в trades.csv"""
        with open(self.file_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                data.get("open_time", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                data.get("symbol"),
                data.get("side"),
                f'{data.get("entry_price", 0):.4f}',
                f'{data.get("take_profit", 0):.4f}',
                f'{data.get("stop_loss", 0):.4f}',
                f'{data.get("exit_price", 0):.4f}',
                f'{data.get("pnl", 0):.4f}',
                f'{data.get("roi", 0):.2f}',
                data.get("duration", 0)
            ])
