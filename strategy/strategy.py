# strategy/strategy.py

import numpy as np
from indicators.indicators import (
    calc_rsi,
    calc_ema,
    calc_atr,
    calc_volume_sma,
    detect_spring,
    detect_upthrust,
)


class Strategy:
    """
    Стратегия принимает pybit HTTP-клиент, OrderManager и настройки.
    """

    def __init__(self, client, orders, settings: dict):
        self.client = client
        self.orders = orders
        self.settings = settings

        self.interval = settings.get("interval", "15")
        self.enable_long = settings.get("enable_long", True)
        self.enable_short = settings.get("enable_short", True)

        self.rsi_period = settings.get("rsi_period", 14)
        self.rsi_long = settings.get("rsi_buy", 30)
        self.rsi_short = settings.get("rsi_sell", 70)

        self.ema_period = settings.get("ema_period", 50)
        self.vol_sma_period = settings.get("volume_sma", 20)
        self.atr_period = settings.get("atr_period", 14)
        self.min_vol_mult = settings.get("volume_mult", 1.0)

        self.tp_long_atr = settings.get("tp_long_atr", 2.5)
        self.sl_long_atr = settings.get("sl_long_atr", 1.2)
        self.tp_short_atr = settings.get("tp_short_atr", 2.5)
        self.sl_short_atr = settings.get("sl_short_atr", 1.2)
        self.min_tp_pct = settings.get("min_tp_pct", 0.01)
        self.min_sl_pct = settings.get("min_sl_pct", 0.01)
        
        self.enable_patterns = settings.get("enable_patterns", True)
        self.use_trend_filter = settings.get("use_trend_filter", True)
        self.min_atr_pct = settings.get("min_atr_pct", 0.3)

    # ===========================================================
    #   ГЛАВНЫЙ МЕТОД СТРАТЕГИИ
    # ===========================================================
    def analyze_symbol(self, symbol: str):
        decisions = []
        try:
            # Загружаем свечи
            resp = self.client.get_kline(
                category="linear",
                symbol=symbol,
                interval=self.interval,
                limit=200,
            )

            if resp.get("retCode") != 0:
                return (
                    symbol,
                    None,
                    {
                        "message": (
                            f"Ошибка Bybit ({resp.get('retCode')}): "
                            f"{resp.get('retMsg')}"
                        ),
                        "indicators": decisions,
                    },
                )

            klines = resp.get("result", {}).get("list", [])

            if not klines:
                return (
                    symbol,
                    None,
                    {
                        "message": "Нет данных по свечам",
                        "indicators": decisions,
                    },
                )

            # ----------------------------
            # парсим OHLCV
            # ----------------------------
            try:
                o = np.array([float(k[1]) for k in klines], dtype=float)
                h = np.array([float(k[2]) for k in klines], dtype=float)
                l = np.array([float(k[3]) for k in klines], dtype=float)
                c = np.array([float(k[4]) for k in klines], dtype=float)
                v = np.array([float(k[5]) for k in klines], dtype=float)
            except (ValueError, TypeError, IndexError) as exc:
                return (
                    symbol,
                    None,
                    {
                        "message": (
                            f"Некорректные данные свечей: {exc}. "
                            "Ожидаем формат [ts, open, high, low, close, volume]."
                        ),
                        "indicators": decisions,
                    },
                )

            last_price = c[-1]

            # ----------------------------
            # Индикация
            # ----------------------------
            rsi = calc_rsi(c, self.rsi_period)
            ema50 = calc_ema(c, self.ema_period)
            atr = calc_atr(h, l, c, self.atr_period)
            vol_sma = calc_volume_sma(v, self.vol_sma_period)

            if rsi is None:
                return (
                    symbol,
                    None,
                    {
                        "message": "Недостаточно данных для RSI",
                        "indicators": decisions,
                    },
                )

            if atr is None:
                return (
                    symbol,
                    None,
                    {
                        "message": "Недостаточно данных для ATR",
                        "indicators": decisions,
                    },
                )

            # Проверка волатильности
            if self.min_atr_pct > 0:
                atr_pct = (atr / last_price) * 100
                if atr_pct < self.min_atr_pct:
                    return (
                        symbol,
                        None,
                        {
                            "message": f"Волатильность слишком низкая ({atr_pct:.2f}% < {self.min_atr_pct}%)",
                            "indicators": decisions,
                        },
                    )

            # расширенный лог
            decisions = []
            decisions.append(f"RSI={rsi:.2f}")

            if ema50 is not None:
                decisions.append(f"EMA{self.ema_period}={ema50:.4f}")
            else:
                decisions.append(f"EMA{self.ema_period}=n/a")

            decisions.append(f"ATR={atr:.6f}")

            if vol_sma is not None:
                decisions.append(f"Volume={v[-1]:.2f}, SMA={vol_sma:.2f}")
            else:
                decisions.append(f"Volume={v[-1]:.2f}, SMA=n/a")

            # ----------------------------
            # проверяем позицию
            # ----------------------------
            if self.orders.has_open_position(symbol, use_cache=True):
                return (
                    symbol,
                    None,
                    {
                        "message": "Позиция уже открыта",
                        "indicators": decisions,
                    },
                )

            # =====================================================
            #                   ЛОНГ (Buy)
            # =====================================================
            if self.enable_long and rsi < self.rsi_long:
                # Проверка объёма
                if vol_sma and v[-1] < vol_sma * self.min_vol_mult:
                    return (
                        symbol,
                        None,
                        {
                            "message": (
                                f"LONG отклонён: объём слабый "
                                f"({v[-1]:.2f} < {vol_sma * self.min_vol_mult:.2f})"
                            ),
                            "indicators": decisions,
                        },
                    )

                # Фильтр тренда по EMA50
                if self.use_trend_filter and ema50 is not None:
                    if last_price < ema50:
                        return (
                            symbol,
                            None,
                            {
                                "message": f"LONG отклонён: цена ниже EMA50 (нисходящий тренд). Цена: {last_price:.4f}, EMA50: {ema50:.4f}",
                                "indicators": decisions,
                            },
                        )

                # Проверка паттерна Spring
                if self.enable_patterns:
                    if not detect_spring(o[-1], h[-1], l[-1], c[-1]):
                        return (
                            symbol,
                            None,
                            {
                                "message": "LONG отклонён: нет паттерна Spring (ложный пробой вниз)",
                                "indicators": decisions,
                            },
                        )

                entry = last_price
                tp = max(
                    entry + atr * self.tp_long_atr,
                    entry * (1 + self.min_tp_pct),
                )
                sl = min(
                    entry - atr * self.sl_long_atr,
                    entry * (1 - self.min_sl_pct),
                )

                pattern_info = ", Spring OK" if self.enable_patterns else ""
                trend_info = f", цена выше EMA50 ({last_price:.4f} > {ema50:.4f})" if (self.use_trend_filter and ema50) else ""
                return (
                    symbol,
                    "long",
                    {
                        "message": f"LONG сигнал: RSI={rsi:.2f}{pattern_info}{trend_info}",
                        "entry": entry,
                        "tp": tp,
                        "sl": sl,
                        "indicators": decisions,
                    },
                )

            # =====================================================
            #                   ШОРТ (Sell)
            # =====================================================
            if self.enable_short and rsi > self.rsi_short:
                # Проверка объёма
                if vol_sma and v[-1] < vol_sma * self.min_vol_mult:
                    return (
                        symbol,
                        None,
                        {
                            "message": (
                                f"SHORT отклонён: объём слабый "
                                f"({v[-1]:.2f} < {vol_sma * self.min_vol_mult:.2f})"
                            ),
                            "indicators": decisions,
                        },
                    )

                # Фильтр тренда по EMA50
                if self.use_trend_filter and ema50 is not None:
                    if last_price > ema50:
                        return (
                            symbol,
                            None,
                            {
                                "message": f"SHORT отклонён: цена выше EMA50 (восходящий тренд). Цена: {last_price:.4f}, EMA50: {ema50:.4f}",
                                "indicators": decisions,
                            },
                        )

                # Проверка паттерна Upthrust
                if self.enable_patterns:
                    if not detect_upthrust(o[-1], h[-1], l[-1], c[-1]):
                        return (
                            symbol,
                            None,
                            {
                                "message": "SHORT отклонён: нет паттерна Upthrust (ложный пробой вверх)",
                                "indicators": decisions,
                            },
                        )

                entry = last_price
                tp = min(
                    entry - atr * self.tp_short_atr,
                    entry * (1 - self.min_tp_pct),
                )
                sl = max(
                    entry + atr * self.sl_short_atr,
                    entry * (1 + self.min_sl_pct),
                )

                pattern_info = ", Upthrust OK" if self.enable_patterns else ""
                trend_info = f", цена ниже EMA50 ({last_price:.4f} < {ema50:.4f})" if (self.use_trend_filter and ema50) else ""
                return (
                    symbol,
                    "short",
                    {
                        "message": f"SHORT сигнал: RSI={rsi:.2f}{pattern_info}{trend_info}",
                        "entry": entry,
                        "tp": tp,
                        "sl": sl,
                        "indicators": decisions,
                    },
                )

            return (
                symbol,
                None,
                {
                    "message": "Сигналов нет.",
                    "indicators": decisions,
                },
            )

        except Exception as e:
            return (
                symbol,
                None,
                {"message": f"Ошибка: {e}", "indicators": decisions},
            )