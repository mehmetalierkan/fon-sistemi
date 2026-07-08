"""Gunluk BIST hisse teknik tarama ve gerekceli oneri uretimi (10.000 TL'lik gunluk islem butcesi icin)."""
from __future__ import annotations

import pandas as pd

from data import stock_client as sc


def build_daily_screening(budget_tl: float = 10_000.0, watchlist: list[str] | None = None) -> pd.DataFrame:
    watchlist = watchlist or sc.WATCHLIST
    rows = []
    for code in watchlist:
        try:
            hist = sc.get_stock_history(code, range_="3mo", interval="1d")
        except Exception:
            continue
        if len(hist) < 25:
            continue

        last = hist.iloc[-1]
        trend_up = bool(
            pd.notna(last["sma20"]) and pd.notna(last["sma50"])
            and last["sma20"] > last["sma50"] and last["kapanis"] > last["sma20"]
        )
        rsi = last["rsi14"]
        rsi_score = 0.0
        if pd.notna(rsi):
            rsi_score = max(0.0, 1 - abs(rsi - 55) / 25)
        vol_ratio = float(last["hacim_orani"]) if pd.notna(last["hacim_orani"]) else 1.0
        momentum_5d = (
            float(last["kapanis"] / hist["kapanis"].iloc[-6] - 1) * 100 if len(hist) > 6 else 0.0
        )
        score = (2.0 if trend_up else 0.0) + rsi_score * 1.5 + min(vol_ratio, 3.0) * 0.5 + max(momentum_5d, 0) * 0.1
        afford_qty = int(budget_tl // last["kapanis"]) if last["kapanis"] else 0

        rows.append(
            {
                "kod": code,
                "fiyat": last["kapanis"],
                "gunluk_getiri_pct": last["gunluk_getiri_pct"],
                "rsi14": rsi,
                "sma20_uzerinde": trend_up,
                "hacim_orani": vol_ratio,
                "momentum_5g_pct": momentum_5d,
                "skor": score,
                "alinabilecek_adet": afford_qty,
                "gerekce": _build_rationale(trend_up, rsi, vol_ratio, momentum_5d),
            }
        )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("skor", ascending=False).reset_index(drop=True)


def _build_rationale(trend_up: bool, rsi: float, vol_ratio: float, momentum_5d: float) -> str:
    parts = []
    if trend_up:
        parts.append("Fiyat 20 ve 50 günlük ortalamaların üzerinde, kısa vadeli trend yukarı yönlü.")
    else:
        parts.append("Fiyat kısa vadeli ortalamaların altında/yakınında, güçlü bir trend sinyali yok.")
    if pd.notna(rsi):
        if rsi > 70:
            durum = "aşırı alım bölgesine yakın (geri çekilme riski)"
        elif rsi < 30:
            durum = "aşırı satım bölgesine yakın (tepki alımı ihtimali)"
        else:
            durum = "nötr/sağlıklı bölgede"
        parts.append(f"RSI(14) {rsi:.0f} - {durum}.")
    if vol_ratio and vol_ratio > 1.3:
        parts.append(f"Hacim, 20 günlük ortalamanın %{(vol_ratio - 1) * 100:.0f} üzerinde - ilgi artışı var.")
    parts.append(f"Son 5 işlem günündeki momentum: %{momentum_5d:.1f}.")
    return " ".join(parts)
