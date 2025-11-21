import os
from dotenv import load_dotenv

load_dotenv()

BYBIT_CONFIG = {
    "api_key": os.getenv("BYBIT_API_KEY"),
    "api_secret": os.getenv("BYBIT_API_SECRET"),

    # ВАЖНО: выбор среды
    "environment": os.getenv("BYBIT_ENV", "testnet").lower(),

    "interval": "15",

    "coins": [
        # Топовые монеты
        "BTCUSDT",
        "ETHUSDT",
        "BNBUSDT",
        "SOLUSDT",
        "XRPUSDT",
        "ADAUSDT",
        "DOGEUSDT",
        "TONUSDT",
        "AVAXUSDT",
        "DOTUSDT",
        "LINKUSDT",
        "UNIUSDT",
        "LTCUSDT",
        "ATOMUSDT",
        "ETCUSDT",
        "XLMUSDT",
        "ALGOUSDT",
        "VETUSDT",
        "FILUSDT",
        "TRXUSDT",
        "AAVEUSDT",
        "APTUSDT",
        "ARBUSDT",
        "OPUSDT",
        "SUIUSDT",
        "STRKUSDT",
        "ZECUSDT",
        "SOONUSDT",
        # Дополнительные популярные пары
        "NEARUSDT",
        "ICPUSDT",
        "INJUSDT",
        "TIAUSDT",
        "SEIUSDT",
        "WLDUSDT",
    ],

    "ema_period": 50,
    "atr_period": 14,
    "atr_min": 0.0005,
    "atr_max": 0.02,

    "volume_sma": 20,
    "volume_mult": 1.5,

    "rsi_period": 14,

    "rsi_buy": 25,
    "rsi_sell": 70,  # Средняя частота: снижено с 75 до 70

    "tp_long_atr": 2.5,
    "sl_long_atr": 1.2,
    "tp_short_atr": 2.5,
    "sl_short_atr": 1.2,
    "min_tp_pct": 0.01,
    "min_sl_pct": 0.01,

    "enable_long": True,  # Включены LONG позиции
    "enable_short": True,
    "enable_tp_sl": True,
    "enable_patterns": False,  # Отключено для средней частоты сигналов
    "use_trend_filter": True,  # Использовать EMA50 для фильтра тренда

    "min_atr_pct": 0.3,  # Минимальная волатильность в % (0.3% = не торговать при низкой волатильности)

    "risk_pct": 2,
    "min_order_usdt": 5,
    "max_position_pct": 10,  # Максимальный размер позиции в % от баланса

    "telegram_token": os.getenv("TELEGRAM_TOKEN"),
    "telegram_chat_id": os.getenv("TELEGRAM_CHAT_ID"),
}
