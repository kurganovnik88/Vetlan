import csv
import os
from datetime import datetime
from pathlib import Path


class StatsLogger:
    """Логирование статистики торговли"""

    def __init__(self, file_path="logs/stats.csv"):
        self.file_path = file_path
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Инициализация файла, если не существует
        if not os.path.exists(file_path):
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Дата",
                    "Символ",
                    "Направление",
                    "Цена входа",
                    "TP",
                    "SL",
                    "Цена выхода",
                    "PnL (USDT)",
                    "ROI (%)",
                    "Результат",
                ])

    def log_trade(self, symbol, direction, entry, tp, sl, exit_price=None, pnl=None, roi=None):
        """Записывает сделку в stats.csv"""
        result = "Открыта"
        if exit_price is not None:
            if pnl is not None:
                result = "Прибыль" if pnl > 0 else "Убыток"
            else:
                result = "Закрыта"

        with open(self.file_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                symbol,
                direction.upper(),
                f"{entry:.6f}",
                f"{tp:.6f}",
                f"{sl:.6f}",
                f"{exit_price:.6f}" if exit_price else "",
                f"{pnl:.4f}" if pnl is not None else "",
                f"{roi:.2f}" if roi is not None else "",
                result,
            ])

    def get_summary(self):
        """Возвращает сводную статистику из файла"""
        if not os.path.exists(self.file_path):
            return None

        trades = []
        with open(self.file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                trades.append(row)

        if not trades:
            return None

        closed_trades = [t for t in trades if t["Результат"] in ["Прибыль", "Убыток"]]
        
        if not closed_trades:
            return {
                "total_trades": len(trades),
                "open_trades": len([t for t in trades if t["Результат"] == "Открыта"]),
                "closed_trades": 0,
            }

        profits = [float(t["PnL (USDT)"]) for t in closed_trades if t["PnL (USDT)"]]
        wins = [p for p in profits if p > 0]
        losses = [p for p in profits if p < 0]

        return {
            "total_trades": len(trades),
            "open_trades": len([t for t in trades if t["Результат"] == "Открыта"]),
            "closed_trades": len(closed_trades),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": (len(wins) / len(closed_trades) * 100) if closed_trades else 0,
            "total_pnl": sum(profits),
            "avg_win": sum(wins) / len(wins) if wins else 0,
            "avg_loss": sum(losses) / len(losses) if losses else 0,
            "profit_factor": abs(sum(wins) / sum(losses)) if losses and sum(losses) != 0 else 0,
        }

