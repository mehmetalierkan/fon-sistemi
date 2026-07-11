"""Yahoo Finance chart API uzerinden BIST hisse verisi (ucretsiz, ek paket gerekmez)."""
from __future__ import annotations

import pandas as pd
import requests

CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# Likit BIST30/BIST100 hisselerinden gunluk tarama icin sabit izleme listesi.
# LOGO (Teknoloji), AYDEM ve GWIND (Yenilenebilir Enerji) sektorel kapsama icin eklendi;
# uclu de Yahoo Finance {KOD}.IS uzerinden canli veri dondurdugu dogrulanarak listeye alindi.
WATCHLIST: list[str] = [
    "THYAO", "ASELS", "GARAN", "AKBNK", "ISCTR", "KCHOL", "SASA", "TUPRS", "EREGL",
    "BIMAS", "SISE", "PGSUS", "FROTO", "TOASO", "YKBNK", "VAKBN", "HALKB", "KOZAL",
    "EKGYO", "ENKAI", "PETKM", "TCELL", "TTKOM", "ARCLK", "DOHOL", "MGROS", "SAHOL",
    "ULKER", "VESTL", "KRDMD", "LOGO", "AYDEM", "GWIND",
]

# Izleme listesindeki her hisse icin ELLE atanmis sabit sektor etiketi.
# Bu bir borsa/resmi kaynak verisi degildir; sirketlerin ana faaliyet alanina gore
# elle hazirlanmis bir haritadir ve Semsiye Portfoy / Sektorel Performans sayfalarinda
# hisse-sektor eslestirmesi icin kullanilir. Etiketler, mumkun oldugunca
# tefas_client._THEME_KEYWORDS'un urettigi fon temasi etiketleriyle ayni tutulmustur
# ki ayni sektor basligi altinda fon + hisse birlikte degerlendirilebilsin.
STOCK_SECTORS: dict[str, str] = {
    "GARAN": "Bankacılık / Finans",
    "AKBNK": "Bankacılık / Finans",
    "ISCTR": "Bankacılık / Finans",
    "YKBNK": "Bankacılık / Finans",
    "VAKBN": "Bankacılık / Finans",
    "HALKB": "Bankacılık / Finans",
    "TUPRS": "Enerji",
    "PETKM": "Enerji",
    "SASA": "Enerji",
    "EREGL": "Sanayi",
    "KRDMD": "Sanayi",
    "SISE": "Sanayi",
    "ARCLK": "Sanayi",
    "VESTL": "Sanayi",
    "TOASO": "Sanayi",
    "FROTO": "Sanayi",
    "THYAO": "Ulaştırma",
    "PGSUS": "Ulaştırma",
    "TCELL": "Telekom",
    "TTKOM": "Telekom",
    "BIMAS": "Perakende / Gıda",
    "MGROS": "Perakende / Gıda",
    "ULKER": "Perakende / Gıda",
    "ASELS": "Savunma Sanayii",
    "EKGYO": "Gayrimenkul / İnşaat",
    "ENKAI": "Gayrimenkul / İnşaat",
    "KCHOL": "Holding",
    "SAHOL": "Holding",
    "DOHOL": "Holding",
    "KOZAL": "Kıymetli Maden",
    "LOGO": "Teknoloji",
    "AYDEM": "Yenilenebilir Enerji",
    "GWIND": "Yenilenebilir Enerji",
}


def _to_ticker(code: str) -> str:
    code = code.upper().strip()
    return code if code.endswith(".IS") else f"{code}.IS"


def get_history_for_ticker(ticker: str, range_: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    """Yahoo Finance chart API'den HAM ticker (suffix eklenmeden) icin OHLCV + indikator getirir.

    BIST disindaki enstrumanlar (doviz, kiymetli maden, ABD hisseleri/endeksleri) icin
    data/global_client.py tarafindan da kullanilir; bu yuzden .IS suffix'i burada eklenmez.
    """
    url = CHART_URL.format(ticker=ticker)
    resp = requests.get(url, params={"range": range_, "interval": interval}, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    payload = resp.json()
    result = (payload.get("chart") or {}).get("result") or []
    if not result:
        return pd.DataFrame(columns=["tarih", "acilis", "yuksek", "dusuk", "kapanis", "hacim"])
    result = result[0]
    timestamps = result.get("timestamp") or []
    quote_list = (result.get("indicators") or {}).get("quote") or [{}]
    quote = quote_list[0] or {}
    df = pd.DataFrame({
        "tarih": pd.to_datetime(timestamps, unit="s"),
        "acilis": quote.get("open"),
        "yuksek": quote.get("high"),
        "dusuk": quote.get("low"),
        "kapanis": quote.get("close"),
        "hacim": quote.get("volume"),
    }).dropna(subset=["kapanis"]).reset_index(drop=True)
    return _add_indicators(df)


def get_quote_for_ticker(ticker: str, display_code: str | None = None) -> dict:
    """Yahoo Finance chart API'den HAM ticker icin guncel fiyat/gun araligi bilgisi getirir."""
    url = CHART_URL.format(ticker=ticker)
    resp = requests.get(url, params={"range": "5d", "interval": "1d"}, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    payload = resp.json()
    result = (payload.get("chart") or {}).get("result") or []
    if not result:
        return {}
    meta = result[0].get("meta") or {}
    return {
        "kod": display_code or ticker,
        "fiyat": meta.get("regularMarketPrice"),
        "onceki_kapanis": meta.get("chartPreviousClose"),
        "gun_yuksek": meta.get("regularMarketDayHigh"),
        "gun_dusuk": meta.get("regularMarketDayLow"),
        "hacim": meta.get("regularMarketVolume"),
        "52h_yuksek": meta.get("fiftyTwoWeekHigh"),
        "52h_dusuk": meta.get("fiftyTwoWeekLow"),
        "ad": meta.get("longName") or meta.get("shortName"),
    }


def get_stock_history(code: str, range_: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    return get_history_for_ticker(_to_ticker(code), range_=range_, interval=interval)


def get_stock_quote(code: str) -> dict:
    return get_quote_for_ticker(_to_ticker(code), display_code=code.upper())


def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    return 100 - (100 / (1 + rs))


def momentum_5g_pct(hist: pd.DataFrame) -> float:
    """Son 5 islem gununun toplam getiri yuzdesi; yetersiz/sifirli veri icin 0.0 doner."""
    if len(hist) > 6 and hist["kapanis"].iloc[-6]:
        return float(hist["kapanis"].iloc[-1] / hist["kapanis"].iloc[-6] - 1) * 100
    return 0.0


def _add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df["sma5"] = df["kapanis"].rolling(5).mean()
    df["sma20"] = df["kapanis"].rolling(20).mean()
    df["sma50"] = df["kapanis"].rolling(50).mean()
    df["rsi14"] = _rsi(df["kapanis"], 14)
    df["gunluk_getiri_pct"] = df["kapanis"].pct_change() * 100
    df["hacim_ort20"] = df["hacim"].rolling(20).mean()
    df["hacim_orani"] = df["hacim"] / df["hacim_ort20"].replace(0, float("nan"))
    return df
