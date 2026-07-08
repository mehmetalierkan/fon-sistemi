"""ABD borsasi + doviz + kiymetli maden verisi (Yahoo Finance chart API, ek paket gerekmez).

BIST disindaki enstrumanlar icin data/stock_client.py'deki HAM ticker fonksiyonlari
(get_quote_for_ticker / get_history_for_ticker) yeniden kullanilir; burada sadece
".IS" suffix'i olmayan ticker'lar (USDTRY=X, GC=F, AAPL, ^GSPC ...) tanimlanir.

Doviz/kiymetli maden yon okumasi TEK bir siteye dayanmaz: Yahoo Finance (birincil, teknik
gostergeler icin) + Frankfurter.app/ECB (doviz icin bagimsiz ikinci kaynak) + GLD/SLV ETF
fiyat hareketi (kiymetli maden icin dolayli ikinci kontrol) birlikte degerlendirilir.
"""
from __future__ import annotations

import datetime as dt

import pandas as pd
import requests

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

# Doviz paritesi ticker'lari (Yahoo Finance "=X" formati) + Frankfurter.app'teki baz para birimi kodu.
FX_PAIRS: dict[str, str] = {
    "USDTRY=X": "Dolar / TL",
    "EURTRY=X": "Euro / TL",
    "GBPTRY=X": "Sterlin / TL",
}
FX_FRANKFURTER_BASE: dict[str, str] = {
    "USDTRY=X": "USD",
    "EURTRY=X": "EUR",
    "GBPTRY=X": "GBP",
}

# Kiymetli maden futures ticker'lari (Yahoo Finance "=F" formati, fiyatlar USD/ons).
METAL_FUTURES: dict[str, str] = {
    "GC=F": "Altın (Ons, USD)",
    "SI=F": "Gümüş (Ons, USD)",
}
# Ikincil/capraz kontrol icin: ayni varligi izleyen ama farkli mekanizmayla islem goren ETF'ler.
METAL_SECONDARY_ETF: dict[str, str] = {
    "GC=F": "GLD",
    "SI=F": "SLV",
}


def get_us_quote(ticker: str) -> dict:
    return sc.get_quote_for_ticker(ticker, display_code=ticker)


def get_us_history(ticker: str, range_: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    return sc.get_history_for_ticker(ticker, range_=range_, interval=interval)


def _frankfurter_trend(base_ccy: str) -> dict | None:
    """Frankfurter.app (Avrupa Merkez Bankasi referans kurlari) uzerinden BAGIMSIZ ikinci kaynak.

    Yahoo Finance disinda, farkli bir kurum/site tarafindan yayinlanan gunluk referans kuru
    kullanilarak son ~10 is gunu icin bagimsiz bir momentum hesaplanir.
    """
    end = dt.date.today()
    start = end - dt.timedelta(days=16)
    try:
        resp = requests.get(
            f"https://api.frankfurter.app/{start.isoformat()}..{end.isoformat()}",
            params={"from": base_ccy, "to": "TRY"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return None
    rates = data.get("rates") or {}
    if len(rates) < 2:
        return None
    items = sorted(rates.items())
    first_val = list(items[0][1].values())[0]
    last_val = list(items[-1][1].values())[0]
    if not first_val:
        return None
    return {
        "kaynak": "Frankfurter.app (Avrupa Merkez Bankası referans kuru)",
        "guncel_deger": last_val,
        "momentum_pct": (last_val / first_val - 1) * 100,
    }


def _metal_secondary_trend(ticker: str) -> dict | None:
    """GLD/SLV ETF fiyat hareketi uzerinden kiymetli maden icin dolayli ikinci kontrol."""
    proxy = METAL_SECONDARY_ETF.get(ticker)
    if not proxy:
        return None
    try:
        hist = get_us_history(proxy, range_="1mo", interval="1d")
    except Exception:
        return None
    if hist.empty or len(hist) < 6:
        return None
    last = hist.iloc[-1]
    return {
        "kaynak": f"Yahoo Finance – {proxy} ETF (aynı varlığı farklı bir enstrümanla izleyen dolaylı çapraz kontrol)",
        "guncel_deger": float(last["kapanis"]),
        "momentum_pct": float(last["kapanis"] / hist["kapanis"].iloc[-6] - 1) * 100,
    }


def _yon_ve_gerekce(
    ad: str,
    trend_up: bool,
    rsi: float,
    momentum_pct: float,
    ikincil: dict | None,
) -> tuple[str, str, str, str]:
    """Birincil (Yahoo teknik) + ikincil kaynak sinyalini birlestirip detayli aciklama uretir.

    Doner: (sinyal, detayli_gerekce, kendi_onerimiz, tutma_suresi)
    """
    rsi_ok = pd.notna(rsi)
    if trend_up and (not rsi_ok or rsi < 70) and momentum_pct > 0:
        birincil_yon = "yukarı"
    elif not trend_up and (not rsi_ok or rsi > 30) and momentum_pct < 0:
        birincil_yon = "aşağı"
    else:
        birincil_yon = "karışık"

    parts = [
        f"**Birincil kaynak (Yahoo Finance, teknik gösterge):** Fiyat {'20/50 günlük ortalamaların üzerinde' if trend_up else '20/50 günlük ortalamaların altında/yakınında'}, "
        f"son 5 günlük momentum %{momentum_pct:.2f}."
    ]
    if rsi_ok:
        if rsi > 70:
            parts.append(f"RSI(14) {rsi:.0f} ile aşırı alım bölgesine yakın — kısa vadede geri çekilme riski artmış olabilir.")
        elif rsi < 30:
            parts.append(f"RSI(14) {rsi:.0f} ile aşırı satım bölgesine yakın — kısa vadede tepki alımı ihtimali artmış olabilir.")
        else:
            parts.append(f"RSI(14) {rsi:.0f} ile nötr/sağlıklı bölgede.")

    ikincil_yon = "karışık"
    if ikincil:
        ik_mom = ikincil.get("momentum_pct")
        if ik_mom is not None:
            ikincil_yon = "yukarı" if ik_mom > 0.15 else ("aşağı" if ik_mom < -0.15 else "yatay")
        parts.append(
            f"**İkincil kaynak ({ikincil['kaynak']}):** güncel değer {ikincil['guncel_deger']:.4f}, "
            f"son ~10 iş gününde momentum %{(ik_mom or 0):.2f} ({ikincil_yon} yönlü)."
        )
    else:
        parts.append("**İkincil kaynak:** şu an çekilemedi, sadece birincil kaynağa dayanılıyor.")

    if birincil_yon in ("yukarı", "aşağı") and ikincil_yon == birincil_yon:
        sinyal = "Al Yönlü" if birincil_yon == "yukarı" else "Sat Yönlü"
        uyum_metni = "İki kaynak da aynı yönü işaret ediyor, bu da okumanın güvenilirliğini artırıyor."
    elif birincil_yon in ("yukarı", "aşağı") and ikincil_yon not in (birincil_yon, "karışık"):
        sinyal = "Nötr"
        uyum_metni = "Birincil ve ikincil kaynak farklı yönleri işaret ediyor; bu çelişki nedeniyle sinyal Nötr'e çekildi."
    elif birincil_yon in ("yukarı", "aşağı"):
        sinyal = "Al Yönlü" if birincil_yon == "yukarı" else "Sat Yönlü"
        uyum_metni = "İkincil kaynak henüz net bir teyit/çelişki vermiyor (yatay), sinyal tek başına birincil kaynağa dayanıyor."
    else:
        sinyal = "Nötr"
        uyum_metni = "Birincil kaynaktaki sinyaller zaten karışık, belirgin bir yön yok."
    parts.append(uyum_metni)

    kendi_onerimiz = (
        f"**Sistemin görüşü:** {sinyal}. {uyum_metni} Bu tamamen kısa vadeli fiyat/teknik gösterge "
        "okumasıdır; haber akışı, faiz kararları veya jeopolitik gelişmeler gibi temel etkenleri içermez. "
        "Kesin bir alım-satım talimatı değil, karar verirken dikkate alabileceğiniz bir girdidir."
    )
    tutma_suresi = (
        "Bu sinyal kısa vadelidir (tipik olarak birkaç gün ile 2 hafta arası geçerliliğini korur); "
        "gösterge bileşenleri (RSI, momentum) hızla değişebileceğinden en az haftada bir tekrar "
        "kontrol edilmesi önerilir. Uzun vadeli tasarruf amacıyla (ör. yıllar içinde altın biriktirme) "
        "tutuluyorsa bu kısa vadeli teknik okumanın önemi azalır."
    )
    return sinyal, " ".join(parts), kendi_onerimiz, tutma_suresi


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

    for ticker, ad in FX_PAIRS.items():
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
        ikincil = _frankfurter_trend(FX_FRANKFURTER_BASE[ticker])
        sinyal, gerekce, kendi_onerimiz, tutma_suresi = _yon_ve_gerekce(ad, trend_up, last["rsi14"], momentum, ikincil)
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
            "kendi_onerimiz": kendi_onerimiz,
            "tutma_suresi": tutma_suresi,
            "ikincil_kaynak": ikincil["kaynak"] if ikincil else "Çekilemedi",
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
        ikincil = _metal_secondary_trend(ticker)
        sinyal, gerekce, kendi_onerimiz, tutma_suresi = _yon_ve_gerekce(ad, trend_up, last["rsi14"], momentum, ikincil)
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
            "kendi_onerimiz": kendi_onerimiz,
            "tutma_suresi": tutma_suresi,
            "ikincil_kaynak": ikincil["kaynak"] if ikincil else "Çekilemedi",
            "gram_try": gram_try,
        })

    return pd.DataFrame(rows)
