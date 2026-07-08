"""Semsiye portfoy kurulumu ve sektorel performans ozetleri.

Sektor/tema eslestirmesi iki kaynaktan gelir:
- Fonlar: tefas_client.categorize_theme (fon UNVANINDAN isim bazli tahmin - kesin veri DEGIL)
- Hisseler: stock_client.STOCK_SECTORS (elle hazirlanmis sabit sektor haritasi)

Skorlama mevcut sayfalarin mantigini yeniden kullanir:
- Fonlar: fund_analysis'teki guvenilirlik filtresi + getiri/volatilite orani yaklasimi
- Hisseler: daily_screener.build_daily_screening'in urettigi teknik skor
"""
from __future__ import annotations

import pandas as pd

from analysis.fund_analysis import (
    MAX_MAKUL_GETIRI_PCT,
    MIN_PORTFOY_BUYUKLUGU,
    MIN_YATIRIMCI_SAYISI,
)
from data import stock_client as sc
from data import tefas_client as tefas

MIN_TOPLAM_ONERI = 5
MAX_TOPLAM_ONERI = 10
MAX_SEKTOR_SAYISI = MAX_TOPLAM_ONERI  # 10'dan fazla sektor girilirse en yuksek yuzdeliler tutulur
MAX_SEKTOR_BASINA_ONERI = 5  # 1-2 sektorluk girislerde toplami 5'e tamamlayabilmek icin

# Fon temasi etiketleri (categorize_theme'in uretebildigi tum degerler).
FUND_THEME_LABELS: list[str] = list(dict.fromkeys(theme for _, theme in tefas._THEME_KEYWORDS)) + ["Genel / Karma"]

# Hisse sektor etiketleri (STOCK_SECTORS haritasindan).
STOCK_SECTOR_LABELS: list[str] = list(dict.fromkeys(sc.STOCK_SECTORS.values()))

# Kullanicinin secebilecegi tum sektor/tema secenekleri (fon temalari + hisse sektorleri).
SECTOR_OPTIONS: list[str] = list(dict.fromkeys([*FUND_THEME_LABELS, *STOCK_SECTOR_LABELS]))

# "Yenilenebilir Enerji" ayri bir fon temasi olarak categorize_theme'de yok
# (oradaki "ENERJİ" anahtar kelimesi genel "Enerji" temasina gider). Bu sektor
# secildiginde fon adinda su kelimeler aranir:
_RENEWABLE_FUND_KEYWORDS = ("YENİLENEBİLİR", "TEMİZ ENERJİ", "GÜNEŞ", "RÜZGAR", "HİDROELEKTRİK")

# Sadece hisse tarafinda var olan, fon adlarindan tahmin EDILEMEYEN sektorler.
STOCK_ONLY_SECTORS = {"Ulaştırma", "Telekom", "Holding"}


def _reliable_funds(fund_returns: pd.DataFrame) -> pd.DataFrame:
    """fund_analysis.build_fund_comparison ile ayni guvenilirlik filtresi + getiri skoru."""
    df = fund_returns.copy()
    guvenilir = (
        (df["portfoyBuyukluk"].fillna(0) >= MIN_PORTFOY_BUYUKLUGU)
        & (df["kisiSayisi"].fillna(0) >= MIN_YATIRIMCI_SAYISI)
        & (df["getiri_1a"].abs() <= MAX_MAKUL_GETIRI_PCT)
        & (df["getiri_3a"].abs() <= MAX_MAKUL_GETIRI_PCT * 2)
    )
    df = df[guvenilir].copy()
    df["skor_getiri"] = df[["getiri_1a", "getiri_3a", "getiri_6a"]].mean(axis=1, skipna=True)
    return df.dropna(subset=["skor_getiri"])


def _fund_theme_for_sector(sector: str) -> str | None:
    """Bir sektor basligini fon temasi etiketine cevirir; fon karsiligi yoksa None."""
    if sector in STOCK_ONLY_SECTORS:
        return None
    if sector == "Perakende / Gıda":
        return "Tarım / Gıda"
    if sector in FUND_THEME_LABELS:
        return sector
    return None


def _fund_candidates(reliable_funds: pd.DataFrame, sector: str) -> pd.DataFrame:
    if reliable_funds.empty:
        return reliable_funds
    if sector == "Yenilenebilir Enerji":
        unvan = reliable_funds["fonUnvan"].fillna("")
        mask = unvan.apply(lambda u: any(k in u.upper() for k in _RENEWABLE_FUND_KEYWORDS))
        df = reliable_funds[mask]
    else:
        theme = _fund_theme_for_sector(sector)
        if theme is None:
            return reliable_funds.iloc[0:0]
        df = reliable_funds[reliable_funds["tema"] == theme]
    return df.sort_values("skor_getiri", ascending=False)


def _stock_candidates(stock_screen: pd.DataFrame, sector: str) -> pd.DataFrame:
    if stock_screen is None or stock_screen.empty:
        return pd.DataFrame()
    df = stock_screen.copy()
    df["sektor"] = df["kod"].map(sc.STOCK_SECTORS)
    return df[df["sektor"] == sector].sort_values("skor", ascending=False)


def _fund_volatility(fon_kodu: str) -> float | None:
    """fund_analysis ile ayni yontem: 3 aylik gunluk NAV getirilerinin yillik std sapmasi (%)."""
    try:
        hist = tefas.get_fund_price_history(fon_kodu, periyod_ay=3)
    except Exception:
        return None
    if len(hist) > 5:
        daily_ret = hist["fiyat"].pct_change().dropna()
        if len(daily_ret) > 0:
            return float(daily_ret.std() * (252 ** 0.5) * 100)
    return None


def _rank_funds_with_volatility(fcand: pd.DataFrame, shortlist_size: int) -> list[dict]:
    """Sektor icindeki en iyi getirili fonlarin volatilitesini cekip getiri/vol oranina gore siralar."""
    records: list[dict] = []
    for _, row in fcand.head(shortlist_size).iterrows():
        vol = _fund_volatility(row["fonKodu"])
        oran = float(row["skor_getiri"]) / vol if vol and vol > 0 else None
        records.append({"row": row, "vol": vol, "oran": oran})
    # Volatilitesi hesaplanabilenler getiri/vol oranina gore once, digerleri getiri skoruna gore sonda.
    records.sort(
        key=lambda r: (r["oran"] is not None, r["oran"] if r["oran"] is not None else float(r["row"]["skor_getiri"])),
        reverse=True,
    )
    return records


def _fund_row(rec: dict, sector: str, amount: float, pick_pct: float) -> dict:
    row, vol, oran = rec["row"], rec["vol"], rec["oran"]
    parts = []
    if pd.notna(row.get("getiri_1a")) and pd.notna(row.get("getiri_3a")):
        parts.append(f"Son 1 ayda %{row['getiri_1a']:.1f}, son 3 ayda %{row['getiri_3a']:.1f} getiri sağladı.")
    if vol is not None:
        parts.append(f"Yıllık volatilitesi yaklaşık %{vol:.1f}.")
    if oran is not None:
        parts.append(f"'{sector}' başlığındaki güvenilir fon adayları arasında getiri/volatilite sıralamasında öne çıktı.")
    else:
        parts.append(f"'{sector}' başlığındaki güvenilir fon adayları arasında ortalama getiri skoruyla öne çıktı.")
    parts.append("(Tema eşleşmesi fon adından tahmindir, kesin sektör verisi değildir.)")
    return {
        "tur": "Fon",
        "kod": row["fonKodu"],
        "ad": row["fonUnvan"],
        "sektor": sector,
        "hedef_pct": pick_pct,
        "tutar_tl": amount,
        "getiri_1a": float(row["getiri_1a"]) if pd.notna(row.get("getiri_1a")) else None,
        "getiri_3a": float(row["getiri_3a"]) if pd.notna(row.get("getiri_3a")) else None,
        "yillik_volatilite_pct": vol,
        "skor": round(float(row["skor_getiri"]), 2),
        "fiyat": None,
        "gerekce": " ".join(parts),
    }


def _stock_row(row: pd.Series, sector: str, amount: float, pick_pct: float) -> dict:
    gerekce = (
        f"'{sector}' sektöründeki izleme listesi hisseleri arasında en yüksek teknik skorlulardan. "
        + str(row.get("gerekce", ""))
    )
    fiyat = float(row["fiyat"]) if pd.notna(row.get("fiyat")) else None
    return {
        "tur": "Hisse",
        "kod": row["kod"],
        "ad": row["kod"],
        "sektor": sector,
        "hedef_pct": pick_pct,
        "tutar_tl": amount,
        "getiri_1a": None,
        "getiri_3a": float(row["momentum_5g_pct"]) if pd.notna(row.get("momentum_5g_pct")) else None,
        "yillik_volatilite_pct": None,
        "skor": round(float(row["skor"]), 2),
        "fiyat": fiyat,
        "gerekce": gerekce,
    }


def build_umbrella_portfolio(
    targets: list[tuple[str, float]],
    budget_tl: float,
    fund_returns: pd.DataFrame,
    stock_screen: pd.DataFrame,
) -> tuple[pd.DataFrame, list[tuple[str, str]]]:
    """Sektor hedeflerinden 5-10 enstrumanlik semsiye portfoy onerisi uretir.

    targets: (sektor, hedef_yuzde) listesi. Yuzdeler toplami 100 degilse normalize edilir.
    Donus: (oneri tablosu, [(seviye, mesaj), ...]) - seviye "warning" ya da "info".
    """
    notes: list[tuple[str, str]] = []

    # 1) Hedefleri temizle: bos/sifir satirlari at, ayni sektoru birlestir.
    merged: dict[str, float] = {}
    for sector, pct in targets:
        if not sector or pct is None or float(pct) <= 0:
            continue
        if sector in merged:
            notes.append(("info", f"'{sector}' birden fazla satırda girildi; yüzdeler toplandı."))
        merged[sector] = merged.get(sector, 0.0) + float(pct)
    if not merged:
        return pd.DataFrame(), [("warning", "Geçerli bir sektör/yüzde satırı girilmedi.")]

    total_pct = sum(merged.values())
    if abs(total_pct - 100.0) > 0.01:
        notes.append(("warning", f"Girilen yüzdelerin toplamı %{total_pct:.1f} idi; otomatik olarak %100'e normalize edildi."))
    weights = {s: p / total_pct * 100.0 for s, p in merged.items()}

    # 2) Cok fazla sektor girildiyse en yuksek yuzdelileri tut (5-10 oneri siniri icin).
    sectors = sorted(weights, key=lambda s: weights[s], reverse=True)
    if len(sectors) > MAX_SEKTOR_SAYISI:
        dropped = sectors[MAX_SEKTOR_SAYISI:]
        sectors = sectors[:MAX_SEKTOR_SAYISI]
        notes.append((
            "warning",
            f"Toplam öneri sınırı ({MAX_TOPLAM_ONERI}) nedeniyle en yüksek yüzdeli {MAX_SEKTOR_SAYISI} sektör tutuldu; "
            f"şu sektörler çıkarıldı: {', '.join(dropped)}.",
        ))

    # 3) Her sektor icin aday havuzlari (fon + hisse).
    reliable = _reliable_funds(fund_returns) if fund_returns is not None and not fund_returns.empty else pd.DataFrame()
    pools: dict[str, tuple[pd.DataFrame, pd.DataFrame]] = {}
    for s in sectors:
        fcand = _fund_candidates(reliable, s) if not reliable.empty else pd.DataFrame()
        scand = _stock_candidates(stock_screen, s)
        if fcand.empty and scand.empty:
            notes.append((
                "warning",
                f"'{s}' için güvenilirlik filtresini geçen fon veya izleme listesinde uygun hisse bulunamadı; "
                "bu sektör portföyden çıkarıldı ve yüzdesi kalan sektörlere dağıtıldı.",
            ))
            continue
        if fcand.empty:
            if s in STOCK_ONLY_SECTORS:
                notes.append(("info", f"'{s}' fon adlarından tahmin edilebilen bir tema değil; bu başlıkta yalnızca hisse adayları değerlendirildi."))
            else:
                notes.append(("info", f"'{s}' temasında güvenilirlik filtresini geçen fon bulunamadı; yalnızca hisse önerisi sunuluyor."))
        elif scand.empty:
            notes.append(("info", f"'{s}' sektöründe izleme listesinde güncel/likit bir BIST hissesi bulunamadı; yalnızca fon önerisi sunuluyor."))
        pools[s] = (fcand, scand)

    if not pools:
        return pd.DataFrame(), notes

    active = [s for s in sectors if s in pools]
    subtotal = sum(weights[s] for s in active)
    weights = {s: weights[s] / subtotal * 100.0 for s in active}

    # 4) Toplam oneri sayisini 5-10 bandina oturt: hedef = min(10, max(5, 2 x sektor sayisi)).
    availability = {
        s: min(len(pools[s][0]) + len(pools[s][1]), MAX_SEKTOR_BASINA_ONERI) for s in active
    }
    target_total = min(MAX_TOPLAM_ONERI, max(MIN_TOPLAM_ONERI, 2 * len(active)))
    target_total = min(target_total, sum(availability.values()))

    counts = {s: 1 for s in active}
    order = sorted(active, key=lambda s: weights[s], reverse=True)
    while sum(counts.values()) < target_total:
        progressed = False
        for s in order:
            if sum(counts.values()) >= target_total:
                break
            if counts[s] < availability[s]:
                counts[s] += 1
                progressed = True
        if not progressed:
            break

    if sum(counts.values()) < MIN_TOPLAM_ONERI:
        notes.append((
            "warning",
            f"Uygun aday sayısı sınırlı olduğu için toplam öneri sayısı {sum(counts.values())} ile "
            f"{MIN_TOPLAM_ONERI}'in altında kaldı.",
        ))

    # 5) Sektor icinde secim: en iyi fon + en iyi hisse donusumlu (cesitlilik icin),
    #    fonlar getiri/volatilite oranina, hisseler teknik skora gore sirali.
    rows: list[dict] = []
    used_codes: set[str] = set()
    for s in order:
        fcand, scand = pools[s]
        k = counts[s]
        fcand = fcand[~fcand["fonKodu"].isin(used_codes)] if not fcand.empty else fcand
        scand = scand[~scand["kod"].isin(used_codes)] if not scand.empty else scand

        fund_ranked = _rank_funds_with_volatility(fcand, shortlist_size=max(3, k)) if not fcand.empty else []
        stock_list = [r for _, r in scand.head(k).iterrows()] if not scand.empty else []

        picks: list[tuple[str, object]] = []
        fi, si = 0, 0
        turn = "fund" if fund_ranked else "stock"
        while len(picks) < k and (fi < len(fund_ranked) or si < len(stock_list)):
            if turn == "fund" and fi < len(fund_ranked):
                picks.append(("fund", fund_ranked[fi]))
                fi += 1
            elif si < len(stock_list):
                picks.append(("stock", stock_list[si]))
                si += 1
            elif fi < len(fund_ranked):
                picks.append(("fund", fund_ranked[fi]))
                fi += 1
            turn = "stock" if turn == "fund" else "fund"

        if not picks:
            continue
        sector_amount = budget_tl * weights[s] / 100.0
        per_amount = sector_amount / len(picks)
        pick_pct = weights[s] / len(picks)
        for kind, item in picks:
            if kind == "fund":
                rows.append(_fund_row(item, s, per_amount, pick_pct))
                used_codes.add(item["row"]["fonKodu"])
            else:
                rows.append(_stock_row(item, s, per_amount, pick_pct))
                used_codes.add(item["kod"])

    result = pd.DataFrame(rows)
    if not result.empty:
        result = result.sort_values(["hedef_pct", "sektor"], ascending=[False, True]).reset_index(drop=True)
    return result, notes


def fund_theme_performance(fund_returns: pd.DataFrame) -> pd.DataFrame:
    """Guvenilir fonlari temalara gore gruplayip ortalama getiri skoruna gore siralar."""
    df = _reliable_funds(fund_returns)
    if df.empty:
        return pd.DataFrame()
    grouped = (
        df.groupby("tema")
        .agg(
            fon_sayisi=("fonKodu", "count"),
            ort_getiri_1a=("getiri_1a", "mean"),
            ort_getiri_3a=("getiri_3a", "mean"),
            ort_skor=("skor_getiri", "mean"),
        )
        .reset_index()
    )
    best = (
        df.sort_values("skor_getiri", ascending=False)
        .groupby("tema", sort=False)
        .first()
        .reset_index()[["tema", "fonKodu", "fonUnvan", "skor_getiri"]]
        .rename(columns={"fonKodu": "en_iyi_kod", "fonUnvan": "en_iyi_ad", "skor_getiri": "en_iyi_skor"})
    )
    grouped = grouped.merge(best, on="tema", how="left")
    return grouped.sort_values("ort_skor", ascending=False).reset_index(drop=True)


def stock_sector_performance(stock_screen: pd.DataFrame) -> pd.DataFrame:
    """Izleme listesi hisselerini sektorlere gore gruplayip ortalama teknik skora gore siralar."""
    if stock_screen is None or stock_screen.empty:
        return pd.DataFrame()
    df = stock_screen.copy()
    df["sektor"] = df["kod"].map(sc.STOCK_SECTORS)
    df = df.dropna(subset=["sektor"])
    if df.empty:
        return pd.DataFrame()
    grouped = (
        df.groupby("sektor")
        .agg(
            hisse_sayisi=("kod", "count"),
            ort_skor=("skor", "mean"),
            ort_momentum_5g=("momentum_5g_pct", "mean"),
        )
        .reset_index()
    )
    best = (
        df.sort_values("skor", ascending=False)
        .groupby("sektor", sort=False)
        .first()
        .reset_index()[["sektor", "kod", "skor"]]
        .rename(columns={"kod": "en_iyi_kod", "skor": "en_iyi_skor"})
    )
    grouped = grouped.merge(best, on="sektor", how="left")
    return grouped.sort_values("ort_skor", ascending=False).reset_index(drop=True)
