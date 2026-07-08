"""ABD borsasi + doviz + kiymetli maden verisi (Yahoo Finance chart API, ek paket gerekmez).

BIST disindaki enstrumanlar icin data/stock_client.py'deki HAM ticker fonksiyonlari
(get_quote_for_ticker / get_history_for_ticker) yeniden kullanilir; burada sadece
".IS" suffix'i olmayan ticker'lar (USDTRY=X, GC=F, AAPL, ^GSPC ...) tanimlanir.
"""
from __future__ import annotations

import pandas as pd

from data import stock_client as sc

GRAM_PER_OUNCE = 31.1034768

# Buyuk/likit ABD hisseleri - gunluk teknik tarama icin sabit izleme listesi.
US_WATCHLIST: list[str] = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "JPM", "XOM", "JNJ",
    "WMT", "V", "PG", "HD", "KO",
]

# ABD hisseleri icin ELLE atanmis sektor etiketi (BIST STOCK_SECTORS ile ayni mantik).
US_SECTORS: dict[str, str] = {
    "AAPL": "Teknoloji",
    "MSFT": "Teknoloji",
    "GOOGL": "Teknoloji",
    "AMZN": "Perakende / Gıda",
    "NVDA": "Teknoloji",
    "META": "Teknoloji",
    "TSLA": "Otomotiv",
    "JPM": "Bankacılık / Finans",
    "XOM": "Enerji",
    "JNJ": "Sağlık",
    "WMT": "Perakende / Gıda",
    "V": "Bankacılık / Finans",
    "PG": "Tüketim Ürünleri",
    "HD": "Perakende / Gıda",
    "KO": "Tüketim Ürünleri",
}

# Ana ABD endeksleri - karsilastirma/benchmark amacli.
US_INDICES: dict[str, str] = {
    "^GSPC": "S&P 500",
    "^IXIC": "Nasdaq Composite",
    "^DJI": "Dow Jones Endüstri",
}

# Doviz paritesi ticker'lari (Yahoo Finance "=X" formati).
FX_PAIRS: dict[str, str] = {
    "USDTRY=X": "Dolar / TL",
    "EURTRY=X": "Euro / TL",
    "GBPTRY=X": "Sterlin / TL",
}

# Kiymetli maden futures ticker'lari (Yahoo Finance "=F" formati, fiyatlar USD/ons).
METAL_FUTURES: dict[str, str] = {
    "GC=F": "Altın (Ons, USD)",
    "SI=F": "Gümüş (Ons, USD)",
}


def get_us_quote(ticker: str) -> dict:
    return sc.get_quote_for_ticker(ticker, display_code=ticker)


def get_us_history(ticker: str, range_: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    return sc.get_history_for_ticker(ticker, range_=range_, interval=interval)


def _signal_from_score(trend_up: bool, rsi: float, momentum_pct: float) -> tuple[str, str]:
    """Basit teknik sinyal (Al / Sat / Nötr) + kisa gerekce - doviz/kiymetli maden tablosu icin."""
    rsi_ok = pd.notna(rsi)
    if trend_up and (not rsi_ok or rsi < 70) and momentum_pct > 0:
        return "Al Yönlü", "Fiyat kısa vadeli ortalamaların üzerinde ve momentum pozitif."
    if not trend_up and (not rsi_ok or rsi > 30) and momentum_pct < 0:
        return "Sat Yönlü", "Fiyat kısa vadeli ortalamaların altında ve momentum negatif."
    return "Nötr", "Karışık sinyaller var, belirgin bir yön yok."


def build_fx_metals_table() -> pd.DataFrame:
    """Doviz paritelerini ve kiymetli madenleri (ons + TL bazli gram) tek tabloda toplar."""
    rows: list[dict] = []
    usdtry = None
    try:
        usdtry_hist = get_us_history("USDTRY=X", range_="3mo", interval="1d")
        if not usdtry_hist.empty:
            usdtry = float(usdtry_hist.iloc[-1]["kapanis"])
    except Exception:
        pass

    for ticker, ad in {**FX_PAIRS}.items():
        try:
            hist = get_us_history(ticker, range_="3mo", interval="1d")
        except Exception:
            continue
        if hist.empty:
            continue
        last = hist.iloc[-1]
        momentum = (
            float(last["kapanis"] / hist["kapanis"].iloc[-6] - 1) * 100 if len(hist) > 6 else 0.0
        )
        trend_up = bool(
            pd.notna(last["sma20"]) and pd.notna(last["sma50"]) and last["sma20"] > last["sma50"]
        )
        sinyal, gerekce = _signal_from_score(trend_up, last["rsi14"], momentum)
        rows.append({
            "kod": ticker.replace("=X", ""),
            "ad": ad,
            "birim": "TL",
            "fiyat": last["kapanis"],
            "gunluk_getiri_pct": last["gunluk_getiri_pct"],
            "momentum_5g_pct": momentum,
            "rsi14": last["rsi14"],
            "sinyal": sinyal,
            "gerekce": gerekce,
        })

    for ticker, ad in METAL_FUTURES.items():
        try:
            hist = get_us_history(ticker, range_="3mo", interval="1d")
        except Exception:
            continue
        if hist.empty:
            continue
        last = hist.iloc[-1]
        momentum = (
            float(last["kapanis"] / hist["kapanis"].iloc[-6] - 1) * 100 if len(hist) > 6 else 0.0
        )
        trend_up = bool(
            pd.notna(last["sma20"]) and pd.notna(last["sma50"]) and last["sma20"] > last["sma50"]
        )
        sinyal, gerekce = _signal_from_score(trend_up, last["rsi14"], momentum)
        ons_usd = float(last["kapanis"])
        gram_try = (ons_usd / GRAM_PER_OUNCE) * usdtry if usdtry else None
        rows.append({
            "kod": ticker.replace("=F", ""),
            "ad": ad,
            "birim": "USD/ons",
            "fiyat": ons_usd,
            "gunluk_getiri_pct": last["gunluk_getiri_pct"],
            "momentum_5g_pct": momentum,
            "rsi14": last["rsi14"],
            "sinyal": sinyal,
            "gerekce": gerekce,
            "gram_try": gram_try,
        })

    return pd.DataFrame(rows)
