"""Yahoo Finance uzerinden yatirim kurulusu (sell-side) analist konsensus verisi.

Bu veri /v10/finance/quoteSummary endpoint'inden gelir ve bir "crumb" (oturum bazli
kisa omurlu anahtar) + cerez gerektirir; herkese acik ama belgelendirilmemis bir
endpoint'tir. Kucuk/az takip edilen BIST hisselerinde analist kapsamasi olmayabilir
(bu durumda None dondurulur, sayfa bunu "kapsam yok" olarak gosterir).

Hangi kurumlar? "recommendationTrend"/"financialData" modulleri Yahoo'nun agregasyonudur
(hangi bankalarin dahil oldugu tek tek belirtilmez, sadece toplam sayilar verilir).
Ancak "upgradeDowngradeHistory" modulu GERCEK kurum adlarini verir (ör. "Morgan Stanley",
"JPMorgan", "Goldman Sachs", "Evercore ISI" gibi) - bu yuzden her ticker icin son
yukseltme/dusurme hareketlerindeki firma adlari da ayrica cekilip gosterilir.
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


_CONSENSUS_TR = {
    "strong_buy": "Güçlü Al", "buy": "Al", "hold": "Tut", "sell": "Sat", "strong_sell": "Güçlü Sat",
}
_ACTION_TR = {"up": "Yükseltti", "down": "Düşürdü", "main": "Korudu", "reit": "Yineledi", "init": "Kapsama Aldı"}


def _build_rationale(rec: dict, moves: list[dict]) -> tuple[str, str, str]:
    """Detayli gerekce, kendi_onerimiz ve tutma_suresi metni uretir."""
    konsensus_tr = _CONSENSUS_TR.get(rec["konsensus"], rec["konsensus"])
    parts = [
        f"**Analist dağılımı:** {int(rec['toplam_analist'])} analistten "
        f"{int(rec['guclu_al'])} Güçlü Al, {int(rec['al'])} Al, {int(rec['tut'])} Tut, "
        f"{int(rec['sat'])} Sat, {int(rec['guclu_sat'])} Güçlü Sat görüşü var; ortalama konsensus **{konsensus_tr}** "
        f"(skor {rec['konsensus_skor']:.2f}/5.0, 1.0=Güçlü Al, 5.0=Güçlü Sat)."
        if rec.get("konsensus_skor") is not None else f"**Konsensus:** {konsensus_tr}."
    ]
    if rec.get("hedef_getiri_pct") is not None:
        yon = "yukarı" if rec["hedef_getiri_pct"] > 0 else "aşağı"
        parts.append(
            f"Ortalama hedef fiyat {rec['hedef_fiyat_ort']:.2f} (en düşük {rec['hedef_fiyat_dusuk']:.2f} — "
            f"en yüksek {rec['hedef_fiyat_yuksek']:.2f}); bu, güncel fiyata göre yaklaşık %{rec['hedef_getiri_pct']:.1f} "
            f"{yon} potansiyele işaret ediyor."
        )
    if moves:
        firms = ", ".join(f"{m['firma']} ({_ACTION_TR.get(m['aksiyon'], m['aksiyon'])}: {m['yeni_derece']})" for m in moves[:5])
        parts.append(f"**Son hareket eden kurumlar:** {firms}.")
    else:
        parts.append("Son dönemde bireysel kurum bazlı bir yükseltme/düşürme hareketi bulunamadı.")

    kendi_onerimiz = (
        f"**Sistemin görüşü:** Analist konsensusu **{konsensus_tr}** yönünde"
        + (f" ve ortalama hedef fiyat mevcut fiyata göre %{rec['hedef_getiri_pct']:.1f} potansiyel gösteriyor. " if rec.get("hedef_getiri_pct") is not None else ". ")
        + "Bu görüş kurumların kendi finansal modellerine dayanır, günlük teknik sinyallerimizle aynı kaynaktan gelmez; "
        "ikisi çelişirse (ör. teknik görünüm kötü ama analistler olumluysa) bunu bir uyarı işareti olarak değil, "
        "farklı zaman ufuklarına bakan iki ayrı bakış açısı olarak değerlendirin."
    )
    tutma_suresi = (
        "Analist hedef fiyatları tipik olarak **12 aylık** bir ufku yansıtır — bu, Günlük İşlem Analizi/ABD "
        "Borsası sayfalarındaki birkaç günlük-haftalık teknik sinyallerden çok daha uzun vadelidir. Kısa vadeli "
        "alım-satım kararları için tek başına yeterli değildir; orta-uzun vadeli pozisyon değerlendirmesi için "
        "daha uygundur. Hedef fiyatlar genellikle çeyreklik bilanço dönemlerinde güncellenir."
    )
    return " ".join(parts), kendi_onerimiz, tutma_suresi


def get_recommendation(ticker: str, retry: bool = True) -> dict | None:
    """Tek bir ticker icin analist konsensus + hedef fiyat + firma bazli hareket bilgisini getirir."""
    session, crumb = _get_session()
    params = {"modules": "recommendationTrend,financialData,upgradeDowngradeHistory"}
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

    history = (entry.get("upgradeDowngradeHistory") or {}).get("history") or []
    moves = []
    for h in sorted(history, key=lambda x: x.get("epochGradeDate", 0), reverse=True):
        firma = h.get("firm")
        if not firma:
            continue
        moves.append({
            "firma": firma,
            "tarih": h.get("epochGradeDate"),
            "aksiyon": h.get("action"),
            "eski_derece": h.get("fromGrade"),
            "yeni_derece": h.get("toGrade"),
            "hedef_fiyat": h.get("currentPriceTarget"),
        })

    rec = {
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
        "son_hareketler": moves[:8],
    }
    gerekce, kendi_onerimiz, tutma_suresi = _build_rationale(rec, moves)
    rec["gerekce"] = gerekce
    rec["kendi_onerimiz"] = kendi_onerimiz
    rec["tutma_suresi"] = tutma_suresi
    return rec


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
