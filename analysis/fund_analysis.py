"""Haftalik fon karsilastirma, skorlama ve gerekceli oneri uretimi."""
from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd

from data import tefas_client as tefas


MIN_PORTFOY_BUYUKLUGU = 10_000_000.0  # TL - kucuk/yeni fonlardaki fiyat anomalilerini elemek icin
MIN_YATIRIMCI_SAYISI = 20
MAX_MAKUL_GETIRI_PCT = 100.0  # bu esigin uzerindeki donemsel getiriler supheli/anomali kabul edilir


def build_fund_comparison(
    fon_tipi: str = "YAT",
    kategori: str | None = None,
    tema: str | None = None,
    top_n: int = 15,
    as_of: dt.date | None = None,
    volatility_shortlist_size: int = 30,
) -> tuple[pd.DataFrame, list[dict]]:
    as_of = as_of or dt.date.today()
    returns_df = tefas.get_universe_returns(as_of, fon_tipi)
    if returns_df.empty:
        return returns_df, []

    if kategori and kategori != "Tümü":
        returns_df = returns_df[returns_df["kategori"] == kategori].copy()
    if tema and tema != "Tümü":
        returns_df = returns_df[returns_df["tema"] == tema].copy()

    # Kucuk/yeni/dusuk likiditeli fonlarda gorulen anormal getiri sicramalarini disla.
    guvenilir = (
        (returns_df["portfoyBuyukluk"].fillna(0) >= MIN_PORTFOY_BUYUKLUGU)
        & (returns_df["kisiSayisi"].fillna(0) >= MIN_YATIRIMCI_SAYISI)
        & (returns_df["getiri_1a"].abs() <= MAX_MAKUL_GETIRI_PCT)
        & (returns_df["getiri_3a"].abs() <= MAX_MAKUL_GETIRI_PCT * 2)
    )
    returns_df["guvenilir_veri"] = guvenilir

    returns_df["kategori_ort_1a"] = returns_df.groupby("kategori")["getiri_1a"].transform("mean")
    returns_df["kategori_persentil_1a"] = returns_df.groupby("kategori")["getiri_1a"].rank(pct=True) * 100
    returns_df["skor_getiri"] = returns_df[["getiri_1a", "getiri_3a", "getiri_6a"]].mean(axis=1, skipna=True)

    candidate_pool = returns_df[returns_df["guvenilir_veri"]]
    if candidate_pool.empty:
        candidate_pool = returns_df
    shortlist = candidate_pool.sort_values("skor_getiri", ascending=False).head(
        min(volatility_shortlist_size, len(candidate_pool))
    )

    vol_map: dict[str, float] = {}
    for code in shortlist["fonKodu"]:
        try:
            hist = tefas.get_fund_price_history(code, periyod_ay=3)
        except Exception:
            continue
        if len(hist) > 5:
            daily_ret = hist["fiyat"].pct_change().dropna()
            if len(daily_ret) > 0:
                vol_map[code] = float(daily_ret.std() * (252 ** 0.5) * 100)

    returns_df["yillik_volatilite_pct"] = returns_df["fonKodu"].map(vol_map)
    returns_df["getiri_volatilite_orani"] = returns_df["skor_getiri"] / returns_df["yillik_volatilite_pct"].replace(0, np.nan)

    alloc_df = tefas.get_fund_allocation_snapshot(as_of, fon_tipi)
    alloc_map = {row["fonKodu"]: row for _, row in alloc_df.iterrows()} if not alloc_df.empty else {}

    ranked = returns_df[returns_df["guvenilir_veri"]].dropna(subset=["yillik_volatilite_pct"]).sort_values(
        "getiri_volatilite_orani", ascending=False
    )
    top = ranked.head(top_n)

    recommendations = []
    for _, row in top.iterrows():
        alloc_row = alloc_map.get(row["fonKodu"])
        breakdown = tefas.allocation_breakdown(alloc_row) if alloc_row is not None else []
        recommendations.append(
            {
                "fonKodu": row["fonKodu"],
                "fonUnvan": row["fonUnvan"],
                "kategori": row["kategori"],
                "tema": row["tema"],
                "getiri_1h": row["getiri_1h"],
                "getiri_1a": row["getiri_1a"],
                "getiri_3a": row["getiri_3a"],
                "getiri_6a": row["getiri_6a"],
                "yillik_volatilite_pct": row["yillik_volatilite_pct"],
                "kategori_persentil_1a": row["kategori_persentil_1a"],
                "varlik_dagilimi": breakdown,
                "gerekce": _build_rationale(row, breakdown),
            }
        )
    return returns_df, recommendations


def _build_rationale(row: pd.Series, breakdown: list[tuple[str, float]]) -> str:
    parts = []
    if pd.notna(row.get("getiri_1a")) and pd.notna(row.get("getiri_3a")):
        parts.append(f"Son 1 ayda %{row['getiri_1a']:.1f}, son 3 ayda %{row['getiri_3a']:.1f} getiri sağladı.")
    if pd.notna(row.get("kategori_persentil_1a")):
        parts.append(
            f"'{row['kategori']}' kategorisinde son 1 aylık getirisiyle fonların "
            f"%{row['kategori_persentil_1a']:.0f}'inden daha iyi performans gösterdi."
        )
    if row.get("tema") and row["tema"] != "Genel / Karma":
        parts.append(f"Sektör/tema odağı (fon adından tahmini): {row['tema']}.")
    if pd.notna(row.get("yillik_volatilite_pct")):
        parts.append(f"Yıllık volatilitesi yaklaşık %{row['yillik_volatilite_pct']:.1f}.")
    if breakdown:
        top3 = ", ".join(f"%{v:.0f} {k}" for k, v in breakdown[:3])
        parts.append(f"Portföy dağılımı: {top3}.")
    return " ".join(parts) if parts else "Yeterli veri bulunamadı."


def get_fund_detail(fon_kodu: str, as_of: dt.date | None = None) -> dict:
    as_of = as_of or dt.date.today()
    history = tefas.get_fund_price_history(fon_kodu, periyod_ay=12)
    alloc_df = tefas.get_fund_allocation_snapshot(as_of, fon_kodu=fon_kodu)
    breakdown = tefas.allocation_breakdown(alloc_df.iloc[0]) if not alloc_df.empty else []
    return {"tarihce": history, "varlik_dagilimi": breakdown}
