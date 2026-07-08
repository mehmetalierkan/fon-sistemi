"""Haftalik fon karsilastirma ve gerekceli oneri sayfasi."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import datetime as dt

import plotly.express as px
import streamlit as st

from analysis import fund_analysis

st.set_page_config(page_title="Haftalık Fon Analizi", page_icon="📈", layout="wide")

st.title("📈 Haftalık Fon Analizi")
st.caption(
    "TEFAS'ın herkese açık verileriyle hesaplanır. Not: TEFAS'ın ücretsiz API'si fonun *varlık sınıfı* "
    "dağılımını (hisse senedi/tahvil/döviz vb. yüzdeleri) verir; fon içindeki spesifik hisse senedi "
    "isimlerini/ağırlıklarını vermez."
)


@st.cache_data(ttl=3600, show_spinner="TEFAS'tan fon verileri çekiliyor (birkaç dakika sürebilir)...")
def _load(fon_tipi: str, kategori: str, top_n: int, as_of_str: str):
    as_of = dt.date.fromisoformat(as_of_str)
    return fund_analysis.build_fund_comparison(fon_tipi=fon_tipi, kategori=kategori, top_n=top_n, as_of=as_of)


@st.cache_data(ttl=3600, show_spinner="Fon detayı yükleniyor...")
def _load_detail(fon_kodu: str, as_of_str: str):
    as_of = dt.date.fromisoformat(as_of_str)
    return fund_analysis.get_fund_detail(fon_kodu, as_of=as_of)


col_a, col_b, col_c, col_d = st.columns([1, 1, 1, 1])
with col_a:
    fon_tipi = st.selectbox("Fon Tipi", ["YAT", "EMK", "BYF"], index=0, help="YAT: Yatırım Fonu, EMK: Emeklilik Fonu, BYF: Borsa Yatırım Fonu")
with col_b:
    kategori = st.selectbox(
        "Kategori",
        ["Tümü", "Hisse Senedi", "Para Piyasası", "Katılım", "Karma / Değişken", "Borçlanma Araçları", "Serbest", "Endeks", "Kıymetli Maden", "Fon Sepeti", "Diğer"],
        index=0,
    )
with col_c:
    top_n = st.number_input("Kaç öneri gösterilsin?", min_value=3, max_value=30, value=10)
with col_d:
    st.write("")
    st.write("")
    if st.button("🔄 Verileri Yenile"):
        st.cache_data.clear()
        st.rerun()

as_of = dt.date.today()

try:
    returns_df, recommendations = _load(fon_tipi, kategori, int(top_n), as_of.isoformat())
except Exception as exc:
    st.error(f"TEFAS verisi çekilirken hata oluştu: {exc}")
    st.stop()

if returns_df.empty:
    st.info("Seçilen kritere uygun fon bulunamadı.")
    st.stop()

st.subheader(f"Öne Çıkan {len(recommendations)} Fon Önerisi")
st.caption("Sıralama: getiri / volatilite oranına göre (yüksek getiri + düşük risk = üstte).")

for rec in recommendations:
    with st.expander(f"**{rec['fonKodu']}** — {rec['fonUnvan']} ({rec['kategori']})", expanded=False):
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("1 Hafta", f"%{rec['getiri_1h']:.1f}" if rec['getiri_1h'] == rec['getiri_1h'] else "-")
        m2.metric("1 Ay", f"%{rec['getiri_1a']:.1f}" if rec['getiri_1a'] == rec['getiri_1a'] else "-")
        m3.metric("3 Ay", f"%{rec['getiri_3a']:.1f}" if rec['getiri_3a'] == rec['getiri_3a'] else "-")
        m4.metric("Yıllık Volatilite", f"%{rec['yillik_volatilite_pct']:.1f}" if rec['yillik_volatilite_pct'] == rec['yillik_volatilite_pct'] else "-")
        st.markdown(f"**Neden bu fon?** {rec['gerekce']}")
        if rec["varlik_dagilimi"]:
            labels = [x[0] for x in rec["varlik_dagilimi"]]
            values = [x[1] for x in rec["varlik_dagilimi"]]
            fig = px.pie(names=labels, values=values, title="Varlık Dağılımı (%)")
            st.plotly_chart(fig, width="stretch", key=f"pie_{rec['fonKodu']}")

st.divider()
st.subheader("Tüm Fon Karşılaştırma Tablosu")
display_cols = [
    "fonKodu", "fonUnvan", "kategori", "getiri_1h", "getiri_1a", "getiri_3a", "getiri_6a",
    "yillik_volatilite_pct", "kategori_persentil_1a",
]
st.dataframe(
    returns_df[display_cols].sort_values("getiri_1a", ascending=False).reset_index(drop=True),
    width="stretch",
    height=400,
)

st.divider()
st.subheader("Fon Detayı")
selected_fund = st.selectbox("Bir fon kodu seçin", sorted(returns_df["fonKodu"].unique()))
if selected_fund:
    detail = _load_detail(selected_fund, as_of.isoformat())
    hist = detail["tarihce"]
    if not hist.empty:
        fig = px.line(hist, x="tarih", y="fiyat", title=f"{selected_fund} - 12 Aylık NAV Geçmişi")
        st.plotly_chart(fig, width="stretch")
    if detail["varlik_dagilimi"]:
        labels = [x[0] for x in detail["varlik_dagilimi"]]
        values = [x[1] for x in detail["varlik_dagilimi"]]
        fig2 = px.pie(names=labels, values=values, title=f"{selected_fund} - Varlık Dağılımı (%)")
        st.plotly_chart(fig2, width="stretch")
