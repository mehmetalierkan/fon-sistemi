"""Gunluk hisse teknik tarama ve gerekceli oneri uretimi (BIST icin 10.000 TL'lik gunluk islem butcesi).

Ayni skorlama formulu (trend + RSI + hacim + momentum), ticker'lara nasil ulasildigi disinda
degismeden, ABD borsasi taramasi (build_us_screening) icin de kullanilir - kriterler her iki
sayfada da birebir aynidir.
"""
from __future__ import annotations

from typing import Callable

import pandas as pd

from data import stock_client as sc


def _score_watchlist(
    watchlist: list[str],
    budget_tl: float,
    history_fn: Callable[[str], pd.DataFrame],
) -> pd.DataFrame:
    rows = []
    for code in watchlist:
        try:
            hist = history_fn(code)
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
                "gerekce": _build_rationale(trend_up, rsi, vol_ratio, momentum_5d, score),
            }
        )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("skor", ascending=False).reset_index(drop=True)


def build_daily_screening(budget_tl: float = 10_000.0, watchlist: list[str] | None = None) -> pd.DataFrame:
    watchlist = watchlist or sc.WATCHLIST
    return _score_watchlist(
        watchlist, budget_tl, lambda code: sc.get_stock_history(code, range_="3mo", interval="1d")
    )


def build_us_screening(budget_usd: float = 1_000.0, watchlist: list[str] | None = None) -> pd.DataFrame:
    """ABD borsasi icin ayni skorlama formulu; fiyatlar USD, butce de USD cinsindendir."""
    from data import global_client as gc

    watchlist = watchlist or gc.US_WATCHLIST
    return _score_watchlist(
        watchlist, budget_usd, lambda code: sc.get_history_for_ticker(code, range_="3mo", interval="1d")
    )


def _build_rationale(trend_up: bool, rsi: float, vol_ratio: float, momentum_5d: float, score: float) -> str:
    parts = []
    if trend_up:
        parts.append(
            "**Trend:** Fiyat, 20 günlük ortalama 50 günlük ortalamanın üzerindeyken kendisi de 20 günlük "
            "ortalamanın üzerinde — bu, hem orta hem kısa vadeli eğilimin yukarı yönlü olduğu anlamına gelir."
        )
    else:
        parts.append(
            "**Trend:** Fiyat kısa vadeli ortalamaların altında/yakınında seyrediyor; net bir yukarı trend "
            "sinyali yok, bu da skoru düşüren en önemli etken."
        )
    if pd.notna(rsi):
        if rsi > 70:
            durum = "aşırı alım bölgesine yakın — kısa vadede kâr satışıyla geri çekilme riski artmış olabilir"
        elif rsi < 30:
            durum = "aşırı satım bölgesine yakın — düşüş hız kesmiş olabilir, tepki alımı ihtimali var"
        else:
            durum = "nötr/sağlıklı bölgede, ne aşırı alım ne aşırı satım baskısı belirgin"
        parts.append(f"**RSI(14):** {rsi:.0f} — {durum}. (0-100 arası; 70 üzeri aşırı alım, 30 altı aşırı satım kabul edilir.)")
    if vol_ratio and vol_ratio > 1.3:
        parts.append(
            f"**Hacim:** Günlük işlem hacmi, son 20 günlük ortalamanın %{(vol_ratio - 1) * 100:.0f} üzerinde — "
            "bu hisseye olan ilginin arttığını, fiyat hareketinin daha fazla katılımcı tarafından desteklendiğini gösterir."
        )
    else:
        parts.append("**Hacim:** Ortalamaya yakın, belirgin bir ilgi artışı/azalışı yok.")
    parts.append(f"**Momentum:** Son 5 işlem gününde toplam %{momentum_5d:.1f} getiri.")
    parts.append(
        f"**Toplam skor {score:.1f}** — bu dört bileşenin ağırlıklı toplamıdır, sıralama bu skora göre yapılır."
    )
    parts.append(
        "**Ne kadar süre için geçerli?** Bu tamamen kısa vadeli bir teknik okumadır; RSI ve hacim gibi "
        "bileşenler gün içinde hızla değişebileceğinden sinyal tipik olarak birkaç gün ile 2-3 hafta arasında "
        "anlamlıdır. Pozisyonu en az haftada bir (idealde her gün, bu sayfa güncellendiğinde) tekrar "
        "değerlendirin; şirket haberleri/bilanço gibi temel gelişmeler bu teknik skora dahil değildir."
    )
    return " ".join(parts)
