"""Yahoo Finance uzerinden yatirim kurulusu (sell-side) analist konsensus verisi.

Bu veri /v10/finance/quoteSummary endpoint'inden gelir ve bir "crumb" (oturum bazli
kisa omurlu anahtar) + cerez gerektirir; herkese acik ama belgelendirilmemis bir
endpoint'tir. Kucuk/az takip edilen BIST hisselerinde analist kapsamasi olmayabilir
(bu durumda None dondurulur, sayfa bunu "kapsam yok" olarak gosterir).
"""
from __future__ import annotations

import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
QUOTE_SUMMARY_URL = "https://query2.finance.yahoo.com/v10/finance/quoteSummary/{ticker}"

_session: requests.Session | None = None
_crumb: str | None = None


def _init_session() -> tuple[requests.Session, str | None]:
    global _session, _crumb
    session = requests.Session()
    session.headers.update(HEADERS)
    try:
        session.get("https://fc.yahoo.com", timeout=15)
    except Exception:
        pass
    crumb = None
    try:
        resp = session.get("https://query2.finance.yahoo.com/v1/test/getcrumb", timeout=15)
        if resp.status_code == 200 and resp.text and "Unauthorized" not in resp.text:
            crumb = resp.text.strip()
    except Exception:
        crumb = None
    _session, _crumb = session, crumb
    return session, crumb


def _get_session() -> tuple[requests.Session, str | None]:
    if _session is None:
        return _init_session()
    return _session, _crumb


def get_recommendation(ticker: str, retry: bool = True) -> dict | None:
    """Tek bir ticker icin analist konsensus + hedef fiyat bilgisini getirir. Kapsam yoksa None."""
    session, crumb = _get_session()
    params = {"modules": "recommendationTrend,financialData"}
    if crumb:
        params["crumb"] = crumb
    try:
        resp = session.get(QUOTE_SUMMARY_URL.format(ticker=ticker), params=params, timeout=20)
    except Exception:
        return None

    if resp.status_code == 401 and retry:
        _init_session()
        return get_recommendation(ticker, retry=False)
    if resp.status_code != 200:
        return None

    try:
        payload = resp.json()
    except Exception:
        return None

    result = ((payload.get("quoteSummary") or {}).get("result")) or []
    if not result:
        return None
    entry = result[0]
    trend_list = (entry.get("recommendationTrend") or {}).get("trend") or []
    current = next((t for t in trend_list if t.get("period") == "0m"), trend_list[0] if trend_list else None)
    fin = entry.get("financialData") or {}
    if not current and not fin:
        return None

    def _raw(d: dict, key: str):
        v = (d.get(key) or {})
        return v.get("raw") if isinstance(v, dict) else v

    strong_buy = current.get("strongBuy", 0) if current else 0
    buy = current.get("buy", 0) if current else 0
    hold = current.get("hold", 0) if current else 0
    sell = current.get("sell", 0) if current else 0
    strong_sell = current.get("strongSell", 0) if current else 0
    total = strong_buy + buy + hold + sell + strong_sell
    if total == 0 and not fin.get("recommendationKey"):
        return None

    current_price = _raw(fin, "currentPrice")
    target_mean = _raw(fin, "targetMeanPrice")
    upside_pct = (
        (target_mean / current_price - 1) * 100
        if current_price and target_mean
        else None
    )

    return {
        "kod": ticker,
        "guclu_al": strong_buy,
        "al": buy,
        "tut": hold,
        "sat": sell,
        "guclu_sat": strong_sell,
        "toplam_analist": total or _raw(fin, "numberOfAnalystOpinions") or 0,
        "konsensus": fin.get("recommendationKey") or "-",
        "konsensus_skor": _raw(fin, "recommendationMean"),
        "guncel_fiyat": current_price,
        "hedef_fiyat_ort": target_mean,
        "hedef_fiyat_yuksek": _raw(fin, "targetHighPrice"),
        "hedef_fiyat_dusuk": _raw(fin, "targetLowPrice"),
        "hedef_getiri_pct": upside_pct,
    }


def get_recommendations_table(tickers: list[str], display_codes: dict[str, str] | None = None):
    import pandas as pd

    display_codes = display_codes or {}
    rows = []
    for ticker in tickers:
        rec = get_recommendation(ticker)
        if rec is None:
            continue
        rec["kod"] = display_codes.get(ticker, ticker)
        rows.append(rec)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("konsensus_skor", ascending=True, na_position="last").reset_index(drop=True)
