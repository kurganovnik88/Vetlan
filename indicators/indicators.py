# indicators/indicators.py
import numpy as np

# ---------------------------
#   RSI
# ---------------------------
def calc_rsi(close_prices, period=14):
    if len(close_prices) < period + 1:
        return None

    deltas = np.diff(close_prices)
    ups = deltas.clip(min=0)
    downs = -deltas.clip(max=0)

    avg_gain = np.mean(ups[:period])
    avg_loss = np.mean(downs[:period])

    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + ups[i]) / period
        avg_loss = (avg_loss * (period - 1) + downs[i]) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return float(rsi)


# ---------------------------
#   EMA
# ---------------------------
def calc_ema(close_prices, period=50):
    if len(close_prices) < period:
        return None

    k = 2 / (period + 1)
    ema = close_prices[0]

    for price in close_prices[1:]:
        ema = price * k + ema * (1 - k)

    return float(ema)


# ---------------------------
#   ATR (Volatility)
# ---------------------------
def calc_atr(high, low, close, period=14):
    if len(close) < period + 1:
        return None

    tr_values = []
    for i in range(1, len(close)):
        tr = max(
            high[i] - low[i],
            abs(high[i] - close[i - 1]),
            abs(low[i] - close[i - 1]),
        )
        tr_values.append(tr)

    if len(tr_values) < period:
        return None

    atr = np.mean(tr_values[-period:])
    return float(atr)


# ---------------------------
#   Volume SMA
# ---------------------------
def calc_volume_sma(volumes, period=20):
    if len(volumes) < period:
        return None
    return float(np.mean(volumes[-period:]))


# ---------------------------
#   SPRING PATTERN (ложный пробой вниз)
# ---------------------------
def detect_spring(o, h, l, c):
    """
    Паттерн Spring (ложный пробой вниз):
      - длинная нижняя тень
      - закрытие выше половины свечи
    """
    body = abs(c - o)
    candle_range = h - l
    lower_shadow = min(o, c) - l

    if candle_range == 0:
        return False

    # условия spring
    if (
        lower_shadow > candle_range * 0.45  
        and c > o                         # бычье закрытие
        and c > (o + c) / 2               # закрытие выше середины
    ):
        return True

    return False


# ---------------------------
#   UPTHRUST PATTERN (ложный пробой вверх)
# ---------------------------
def detect_upthrust(o, h, l, c):
    """
    Паттерн Upthrust (ложный пробой вверх):
      - длинная верхняя тень
      - закрытие ниже половины свечи
    """
    body = abs(c - o)
    candle_range = h - l
    upper_shadow = h - max(o, c)

    if candle_range == 0:
        return False

    if (
        upper_shadow > candle_range * 0.45
        and c < o                         # медвежье закрытие
        and c < (o + c) / 2               # закрытие ниже середины
    ):
        return True

    return False
