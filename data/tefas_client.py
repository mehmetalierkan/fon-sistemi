"""TEFAS (tefas.gov.tr) genel-erisimli API istemcisi.

Bu istemci TEFAS'in resmi olmayan ama herkese acik JSON API'sini kullanir.
Fon icindeki spesifik hisse senedi agirliklari bu API'de YOKTUR - sadece
varlik sinifi bazinda dagilim (hisse senedi %, devlet tahvili %, ...) verilir.
"""
from __future__ import annotations

import datetime as dt
from functools import lru_cache

import pandas as pd
import requests

BASE_URL = "https://www.tefas.gov.tr/api/funds"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
}

# TEFAS varlik dagilimi alan kodlari -> okunabilir Turkce etiketler.
# Kaynak: TEFAS dagilimSiraliGetirT yaniti (53 kolon, cogu bos/null doner).
DIST_FIELD_LABELS: dict[str, str] = {
    "hs": "Hisse Senedi",
    "dt": "Devlet Tahvili",
    "hb": "Hazine Bonosu",
    "fb": "Finansman Bonosu",
    "ost": "Özel Sektör Tahvili",
    "bb": "Banka Bonosu",
    "vdm": "Varlığa Dayalı Menkul Kıymet",
    "eut": "Eurobond",
    "kibd": "Kamu Dış Borçlanma",
    "osdb": "Özel Sektör Dış Borçlanma",
    "kba": "Döviz Ödemeli Kamu İç Borçlanma",
    "dot": "Döviz Ödemeli Bono",
    "db": "Döviz Ödemeli Tahvil",
    "tpp": "Takasbank Para Piyasası",
    "bpp": "BIST Para Piyasası",
    "btaa": "BIST Vadeli İşlem (Alım Taahhüdü)",
    "btas": "BIST Vadeli İşlem (Satım Taahhüdü)",
    "r": "Repo",
    "tr": "Ters Repo",
    "vm": "Vadeli Mevduat",
    "vmtl": "Vadeli Mevduat (TL)",
    "vmd": "Vadeli Mevduat (Döviz)",
    "vmau": "Vadeli Mevduat (Altın)",
    "kh": "Katılma Hesabı",
    "khtl": "Katılma Hesabı (TL)",
    "khd": "Katılma Hesabı (Döviz)",
    "khau": "Katılma Hesabı (Altın)",
    "kks": "Kamu Kira Sertifikası",
    "kkstl": "Kamu Kira Sertifikası (TL)",
    "kksd": "Kamu Kira Sertifikası (Döviz)",
    "kksyd": "Kamu Kira Sertifikası (Yabancı Döviz)",
    "osks": "Özel Sektör Kira Sertifikası",
    "oksyd": "Özel Sektör Kira Sertifikası (Yabancı)",
    "km": "Kıymetli Maden",
    "kmbyf": "Kıymetli Maden ETF",
    "kmkba": "Kıymetli Maden Kamu Borçlanma",
    "kmkks": "Kıymetli Maden Kira Sertifikası",
    "ymk": "Yabancı Menkul Kıymet",
    "yba": "Yabancı Borçlanma Aracı",
    "ybkb": "Yabancı Kamu Borçlanma",
    "ybosb": "Yabancı Özel Sektör Borçlanma",
    "yhs": "Yabancı Hisse Senedi",
    "ybyf": "Yabancı ETF",
    "fkb": "Fon Katılma Belgesi",
    "yyf": "Yatırım Fonu Katılma Payı",
    "byf": "Borsa Yatırım Fonu (ETF)",
    "gykb": "Gayrimenkul Yatırım Fonu",
    "gyy": "Gayrimenkul Yatırımı",
    "gsykb": "Girişim Sermayesi Yatırım Fonu",
    "gsyy": "Girişim Sermayesi Yatırımı",
    "t": "Türev Araçlar",
    "vint": "Vadeli İşlem Nakit Teminatı",
    "gas": "Gayrimenkul Sertifikası",
    "d": "Diğer",
}

# Fon unvanindaki anahtar kelimelere gore kaba kategori tahmini.
# TEFAS'in genel bilgi API'si kategori alani dondurmedigi icin heuristik kullanilir.
_CATEGORY_KEYWORDS: list[tuple[str, str]] = [
    ("PARA PİYASASI", "Para Piyasası"),
    ("KATILIM", "Katılım"),
    ("HİSSE SENEDİ", "Hisse Senedi"),
    ("ENDEKS", "Endeks"),
    ("BORÇLANMA ARAÇLARI", "Borçlanma Araçları"),
    ("SERBEST", "Serbest"),
    ("KARMA", "Karma / Değişken"),
    ("DEĞİŞKEN", "Karma / Değişken"),
    ("ALTIN", "Kıymetli Maden"),
    ("KIYMETLİ MADEN", "Kıymetli Maden"),
    ("FON SEPETİ", "Fon Sepeti"),
    ("GAYRİMENKUL", "Gayrimenkul"),
    ("GİRİŞİM SERMAYESİ", "Girişim Sermayesi"),
]


def categorize_fund(fon_unvan: str) -> str:
    unvan = (fon_unvan or "").upper()
    for keyword, category in _CATEGORY_KEYWORDS:
        if keyword in unvan:
            return category
    return "Diğer"


def _post(endpoint: str, payload: dict) -> list[dict]:
    resp = requests.post(f"{BASE_URL}/{endpoint}", json=payload, headers=HEADERS, timeout=25)
    resp.raise_for_status()
    data = resp.json()
    if data.get("errorMessage"):
        raise RuntimeError(f"TEFAS API hatasi ({endpoint}): {data['errorMessage']}")
    return data.get("resultList") or []


def _base_body(fon_tipi: str, fon_kodu: str, bas_tarih: str, bit_tarih: str, bit_sira: int = 300_000) -> dict:
    return {
        "fonTipi": fon_tipi,
        "fonKodu": fon_kodu,
        "aramaMetni": None,
        "fonTurKod": None,
        "fonGrubu": None,
        "sfonTurKod": None,
        "fonTurAciklama": None,
        "kurucuKod": None,
        "basTarih": bas_tarih,
        "bitTarih": bit_tarih,
        "basSira": 1,
        "bitSira": bit_sira,
        "dil": "TR",
        "sFonTurKod": "",
        "fonKod": "",
        "fonGrup": "",
        "fonUnvanTip": "",
    }


def _fmt(d: dt.date) -> str:
    return d.strftime("%Y%m%d")


def get_price_snapshot(as_of: dt.date, fon_tipi: str = "YAT", fon_kodu: str = "", window_days: int = 6) -> pd.DataFrame:
    """as_of tarihine en yakin (<=) islem gunundeki fon fiyatlarini, TUM fon evreni icin tek cagrida doner.

    TEFAS API'si tarih araligini 1 ay ile sinirliyor; kisa bir pencere (varsayilan 6 gun)
    hafta sonu/resmi tatil bosluklarini gecmeye yeter.
    """
    start = as_of - dt.timedelta(days=window_days)
    body = _base_body(fon_tipi, fon_kodu, _fmt(start), _fmt(as_of))
    rows = _post("fonGnlBlgSiraliGetir", body)
    if not rows:
        return pd.DataFrame(columns=["fonKodu", "fonUnvan", "tarih", "fiyat", "portfoyBuyukluk", "kisiSayisi"])
    df = pd.DataFrame(rows)
    df["tarih"] = pd.to_datetime(df["tarih"])
    df = df.sort_values("tarih").groupby("fonKodu", as_index=False).last()
    return df[["fonKodu", "fonUnvan", "tarih", "fiyat", "portfoyBuyukluk", "kisiSayisi"]]


def get_universe_returns(as_of: dt.date | None = None, fon_tipi: str = "YAT") -> pd.DataFrame:
    """Tum fon evreni icin 1 hafta / 1 ay / 3 ay / 6 ay getiri yuzdelerini hesaplar.

    Her donem icin TEK bir toplu API cagrisi yapilir (fon basina degil), bu yuzden
    ~2000 fonluk evren icin toplam ~5 cagriyla calisir.
    """
    as_of = as_of or dt.date.today()
    now_df = get_price_snapshot(as_of, fon_tipi)
    if now_df.empty:
        return now_df

    horizons = {
        "getiri_1h": as_of - dt.timedelta(weeks=1),
        "getiri_1a": as_of - dt.timedelta(days=30),
        "getiri_3a": as_of - dt.timedelta(days=91),
        "getiri_6a": as_of - dt.timedelta(days=182),
    }

    merged = now_df.rename(columns={"fiyat": "fiyat_guncel", "tarih": "tarih_guncel"})
    for col, target_date in horizons.items():
        past_df = get_price_snapshot(target_date, fon_tipi, window_days=10)
        past_df = past_df.rename(columns={"fiyat": "_fiyat_gecmis"})[["fonKodu", "_fiyat_gecmis"]]
        merged = merged.merge(past_df, on="fonKodu", how="left")
        merged[col] = (merged["fiyat_guncel"] / merged["_fiyat_gecmis"] - 1.0) * 100.0
        merged = merged.drop(columns=["_fiyat_gecmis"])

    merged["kategori"] = merged["fonUnvan"].map(categorize_fund)
    return merged


def get_fund_allocation_snapshot(as_of: dt.date | None = None, fon_tipi: str = "YAT", fon_kodu: str = "") -> pd.DataFrame:
    """Tum fon evreni (ya da tek bir fon) icin varlik sinifi dagilimini (%), en son islem gunu itibariyla doner."""
    as_of = as_of or dt.date.today()
    start = as_of - dt.timedelta(days=6)
    body = _base_body(fon_tipi, fon_kodu, _fmt(start), _fmt(as_of))
    rows = _post("dagilimSiraliGetirT", body)
    if not rows:
        return pd.DataFrame(columns=["fonKodu", "fonUnvan", "tarih"])
    df = pd.DataFrame(rows)
    df["tarih"] = pd.to_datetime(df["tarih"])
    df = df.sort_values("tarih").groupby("fonKodu", as_index=False).last()
    if fon_kodu:
        df = df[df["fonKodu"] == fon_kodu]
    return df


def allocation_breakdown(row: pd.Series, min_pct: float = 0.5) -> list[tuple[str, float]]:
    """Bir fon satirindan, sifir/None olmayan varlik siniflarini buyukten kucuge sirali dondurur."""
    result = []
    for code, label in DIST_FIELD_LABELS.items():
        if code not in row:
            continue
        val = row[code]
        if pd.notna(val) and val >= min_pct:
            result.append((label, float(val)))
    return sorted(result, key=lambda x: x[1], reverse=True)


def get_fund_price_history(fon_kodu: str, periyod_ay: int = 6) -> pd.DataFrame:
    """Tek bir fonun gunluk NAV gecmisini doner (grafik/volatilite hesabi icin).

    periyod_ay: TEFAS API'sinde izin verilen degerler {1, 3, 6, 12, 36, 60}.
    """
    allowed = {1, 3, 6, 12, 36, 60}
    if periyod_ay not in allowed:
        periyod_ay = min(allowed, key=lambda x: abs(x - periyod_ay))
    body = {"fonKodu": fon_kodu, "dil": "TR", "periyod": periyod_ay}
    rows = _post("fonFiyatBilgiGetir", body)
    if not rows:
        return pd.DataFrame(columns=["fonKodu", "fonUnvan", "tarih", "fiyat"])
    df = pd.DataFrame(rows)
    df["tarih"] = pd.to_datetime(df["tarih"])
    return df.sort_values("tarih").reset_index(drop=True)
