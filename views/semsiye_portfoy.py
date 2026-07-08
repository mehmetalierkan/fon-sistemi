"""Sektor/tema hedefli semsiye portfoy olusturma sayfasi (fon + hisse karisik oneri)."""
import datetime as dt

import pandas as pd
import plotly.express as px
import streamlit as st

from analysis import daily_screener, umbrella
from data import tefas_client
from ui import CHART_COLORS, cap_categories, gradient_title

gradient_title("Şemsiye Portföy Oluşturucu", "🌂")
st.caption(
    "Sektör/tema hedeflerinizi yüzdelerle girin (ör. %10 Teknoloji, %50 Yenilenebilir Enerji); sistem her "
    "başlık için TEFAS fonları ve BIST izleme listesindeki hisseler arasından mevcut skorlama kriterleriyle "
    "en iyi adayları seçip bütçenizi dağıtır. Toplam öneri sayısı her zaman **5 ile 10 arasında** tutulur. "
    "**Önemli sınır:** fon-sektör eşleşmesi fonun adından tahmindir (TEFAS kesin sektör verisi vermez), "
    "hisse-sektör eşleşmesi ise elle hazırlanmış sabit bir haritadan gelir. Kriterlerin tam açıklaması için "
    "sol menüden **🧭 Nasıl Değerlendiriyoruz?** sayfasına bakabilirsiniz."
)
st.warning(
    "⚠️ Bu bir otomatik alım-satım sistemi değildir ve yatırım tavsiyesi değildir. Öneriler geçmiş "
    "performansa dayalı otomatik bir taramadır; tüm alım-satım kararları ve sorumluluk size aittir."
)

col_a, col_b = st.columns([1, 3])
with col_a:
    budget = st.number_input("Toplam Bütçe (TL)", min_value=1_000.0, value=30_000.0, step=1_000.0)
    if st.button("🔄 Verileri Yenile"):
        st.cache_data.clear()
        st.rerun()

st.subheader("Hedef Sektör / Tema Dağılımı")
st.caption(
    "Tablodan satır ekleyip çıkarabilirsiniz. Yüzdelerin toplamı 100 değilse otomatik normalize edilir "
    "ve bu size bildirilir."
)

_DEFAULT_TARGETS = pd.DataFrame(
    [
        {"Sektör / Tema": "Teknoloji", "Hedef %": 10.0},
        {"Sektör / Tema": "Yenilenebilir Enerji", "Hedef %": 50.0},
        {"Sektör / Tema": "Bankacılık / Finans", "Hedef %": 25.0},
        {"Sektör / Tema": "Kıymetli Maden", "Hedef %": 15.0},
    ]
)
edited = st.data_editor(
    _DEFAULT_TARGETS,
    num_rows="dynamic",
    width="stretch",
    column_config={
        "Sektör / Tema": st.column_config.SelectboxColumn(
            "Sektör / Tema",
            options=umbrella.SECTOR_OPTIONS,
            required=True,
            help="Fon temaları (fon adından tahmin) + hisse sektörleri (sabit harita) birleşik liste.",
        ),
        "Hedef %": st.column_config.NumberColumn("Hedef %", min_value=0.0, max_value=100.0, step=5.0),
    },
    key="hedef_editor",
)

targets: list[tuple[str, float]] = []
for _, r in edited.iterrows():
    s, p = r.get("Sektör / Tema"), r.get("Hedef %")
    if isinstance(s, str) and s and pd.notna(p) and float(p) > 0:
        targets.append((s, float(p)))

if not targets:
    st.info("En az bir sektör/tema satırı girin (yüzdesi 0'dan büyük olmalı).")
    st.stop()


@st.cache_data(ttl=3600, show_spinner="TEFAS'tan fon evreni çekiliyor (birkaç dakika sürebilir)...")
def _load_funds(as_of_str: str):
    return tefas_client.get_universe_returns(dt.date.fromisoformat(as_of_str))


@st.cache_data(ttl=900, show_spinner="BIST hisseleri taranıyor...")
def _load_stocks():
    return daily_screener.build_daily_screening()


@st.cache_data(ttl=3600, show_spinner="Şemsiye portföy oluşturuluyor...")
def _build(targets_t: tuple, budget_tl: float, as_of_str: str):
    funds = _load_funds(as_of_str)
    stocks = _load_stocks()
    return umbrella.build_umbrella_portfolio(list(targets_t), budget_tl, funds, stocks)


as_of = dt.date.today()
try:
    portfolio_df, notes = _build(tuple(targets), float(budget), as_of.isoformat())
except Exception as exc:
    st.error(f"Veri çekilirken hata oluştu: {exc}")
    st.stop()

for level, text in notes:
    (st.warning if level == "warning" else st.info)(text)

if portfolio_df.empty:
    st.info("Girilen hedeflere uygun öneri oluşturulamadı. Farklı sektörler deneyin veya verileri yenileyin.")
    st.stop()

st.divider()
st.subheader(f"Önerilen Şemsiye Portföy ({len(portfolio_df)} enstrüman)")

fon_sayisi = int((portfolio_df["tur"] == "Fon").sum())
hisse_sayisi = int((portfolio_df["tur"] == "Hisse").sum())
m1, m2, m3, m4 = st.columns(4)
m1.metric("Toplam Öneri", f"{len(portfolio_df)} enstrüman")
m2.metric("Fon / Hisse", f"{fon_sayisi} fon · {hisse_sayisi} hisse")
m3.metric("Sektör Sayısı", f"{portfolio_df['sektor'].nunique()}")
m4.metric("Dağıtılan Bütçe", f"{portfolio_df['tutar_tl'].sum():,.0f} TL")

for _, row in portfolio_df.iterrows():
    ikon = "🏦" if row["tur"] == "Fon" else "📊"
    baslik = f"{ikon} **{row['kod']}** · {row['tur']} · {row['sektor']} — {row['tutar_tl']:,.0f} TL (%{row['hedef_pct']:.1f})"
    with st.expander(baslik, expanded=False):
        if row["tur"] == "Fon":
            st.markdown(f"**{row['ad']}**")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("1 Ay Getiri", f"%{row['getiri_1a']:.1f}" if pd.notna(row["getiri_1a"]) else "-")
            c2.metric("3 Ay Getiri", f"%{row['getiri_3a']:.1f}" if pd.notna(row["getiri_3a"]) else "-")
            c3.metric(
                "Yıllık Volatilite",
                f"%{row['yillik_volatilite_pct']:.1f}" if pd.notna(row["yillik_volatilite_pct"]) else "-",
            )
            c4.metric("Getiri Skoru", f"{row['skor']:.1f}")
        else:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Güncel Fiyat", f"{row['fiyat']:.2f} TL" if pd.notna(row["fiyat"]) else "-")
            c2.metric("Teknik Skor", f"{row['skor']:.1f}")
            c3.metric("5 Gün Momentum", f"%{row['getiri_3a']:.1f}" if pd.notna(row["getiri_3a"]) else "-")
            adet = int(row["tutar_tl"] // row["fiyat"]) if pd.notna(row["fiyat"]) and row["fiyat"] else 0
            c4.metric("Ayrılan Tutarla", f"{adet} adet")
        st.markdown(f"**Neden bu öneri?** {row['gerekce']}")

st.divider()
st.subheader("Gerçekleşen Dağılım")
col_g1, col_g2 = st.columns(2)
with col_g1:
    sektor_dagilim = (
        portfolio_df.groupby("sektor")["tutar_tl"].sum().sort_values(ascending=False)
    )
    capped = cap_categories([(k, float(v)) for k, v in sektor_dagilim.items()])
    fig = px.pie(
        names=[x[0] for x in capped],
        values=[x[1] for x in capped],
        title="Sektör Bazında Dağılım (TL)",
        color_discrete_sequence=CHART_COLORS,
    )
    st.plotly_chart(fig, width="stretch")
with col_g2:
    tur_dagilim = portfolio_df.groupby("tur")["tutar_tl"].sum().sort_values(ascending=False)
    fig2 = px.pie(
        names=list(tur_dagilim.index),
        values=[float(v) for v in tur_dagilim.values],
        title="Fon / Hisse Dağılımı (TL)",
        color_discrete_sequence=CHART_COLORS,
    )
    st.plotly_chart(fig2, width="stretch")

st.subheader("Özet Tablo")
ozet = portfolio_df[
    ["tur", "kod", "ad", "sektor", "hedef_pct", "tutar_tl", "getiri_1a", "getiri_3a", "yillik_volatilite_pct", "skor"]
].rename(
    columns={
        "tur": "Tür",
        "kod": "Kod",
        "ad": "Ad",
        "sektor": "Sektör / Tema",
        "hedef_pct": "Pay %",
        "tutar_tl": "Tutar (TL)",
        "getiri_1a": "1A Getiri % (fon)",
        "getiri_3a": "3A Getiri % / 5G Momentum %",
        "yillik_volatilite_pct": "Yıllık Vol. % (fon)",
        "skor": "Skor",
    }
)
st.dataframe(ozet, width="stretch")
st.caption(
    "Bu tablo bir anlık görüntüdür (snapshot); fon evreni 1 saat, hisse taraması 15 dakika önbelleklenir. "
    "**🔄 Verileri Yenile** ile güncel veri çekebilirsiniz."
)
