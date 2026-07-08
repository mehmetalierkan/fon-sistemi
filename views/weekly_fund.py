"""Haftalik fon karsilastirma ve gerekceli oneri sayfasi."""
import datetime as dt

import plotly.express as px
import streamlit as st

from analysis import fund_analysis
from ui import CHART_COLORS, cap_categories, gradient_title

gradient_title("Haftalık Fon Analizi", "📈")
st.caption(
    "TEFAS'ın herkese açık verileriyle hesaplanır. Not: TEFAS'ın ücretsiz API'si fonun *varlık sınıfı* "
    "dağılımını (hisse senedi/tahvil/döviz vb. yüzdeleri) verir; fon içindeki spesifik hisse senedi "
    "isimlerini/ağırlıklarını vermez. **Sektör/Tema** filtresi fonun adından tahmin edilir (ör. 'Amerika "
    "Hisse Senedi Fonu' → Amerika), TEFAS'tan gelen kesin bir sektör verisi değildir."
)
st.page_link("views/methodology.py", label="🧭 Kriterlerin tam açıklaması için Nasıl Değerlendiriyoruz? sayfasına gidin", icon="🧭")


@st.cache_data(ttl=3600, show_spinner="TEFAS'tan fon verileri çekiliyor (birkaç dakika sürebilir)...")
def _load(fon_tipi: str, kategori: str, tema: str, top_n: int, as_of_str: str):
    as_of = dt.date.fromisoformat(as_of_str)
    return fund_analysis.build_fund_comparison(
        fon_tipi=fon_tipi, kategori=kategori, tema=tema, top_n=top_n, as_of=as_of
    )


@st.cache_data(ttl=3600, show_spinner="Fon detayı yükleniyor...")
def _load_detail(fon_kodu: str, as_of_str: str):
    as_of = dt.date.fromisoformat(as_of_str)
    return fund_analysis.get_fund_detail(fon_kodu, as_of=as_of)


def _pie(breakdown, title, key=None):
    capped = cap_categories(breakdown)
    labels = [x[0] for x in capped]
    values = [x[1] for x in capped]
    fig = px.pie(names=labels, values=values, title=title, color_discrete_sequence=CHART_COLORS)
    st.plotly_chart(fig, width="stretch", key=key)


THEME_OPTIONS = [
    "Tümü", "Genel / Karma", "Amerika Hisse Senedi", "Avrupa Hisse Senedi", "Asya Hisse Senedi",
    "Çin Hisse Senedi", "Hindistan Hisse Senedi", "Japonya Hisse Senedi", "Küresel / Yabancı",
    "Bankacılık / Finans", "Teknoloji", "Sanayi", "Enerji", "Sağlık", "Gayrimenkul / İnşaat",
    "Tarım / Gıda", "Savunma Sanayii", "Temettü Odaklı", "Sürdürülebilirlik / ESG",
    "Kıymetli Maden", "Endeks (BIST)", "Girişim Sermayesi", "Katılım / Faizsiz",
]

col_a, col_b, col_c, col_d, col_e = st.columns([1, 1, 1, 0.8, 1])
with col_a:
    fon_tipi = st.selectbox("Fon Tipi", ["YAT", "EMK", "BYF"], index=0, help="YAT: Yatırım Fonu, EMK: Emeklilik Fonu, BYF: Borsa Yatırım Fonu")
with col_b:
    kategori = st.selectbox(
        "Kategori",
        ["Tümü", "Hisse Senedi", "Para Piyasası", "Katılım", "Karma / Değişken", "Borçlanma Araçları", "Serbest", "Endeks", "Kıymetli Maden", "Fon Sepeti", "Diğer"],
        index=0,
    )
with col_c:
    tema = st.selectbox(
        "Sektör / Tema",
        THEME_OPTIONS,
        index=0,
        help="Fon adından tahmin edilen sektör/tema odağı - TEFAS'ın kesin bir sektör verisi yok, bu bir isim bazlı tahmindir.",
    )
with col_d:
    top_n = st.number_input("Kaç öneri?", min_value=3, max_value=30, value=10)
with col_e:
    st.write("")
    st.write("")
    if st.button("🔄 Verileri Yenile"):
        st.cache_data.clear()
        st.rerun()

as_of = dt.date.today()

try:
    returns_df, recommendations = _load(fon_tipi, kategori, tema, int(top_n), as_of.isoformat())
except Exception as exc:
    st.error(f"TEFAS verisi çekilirken hata oluştu: {exc}")
    st.stop()

if returns_df.empty:
    st.info("Seçilen kritere uygun fon bulunamadı.")
    st.stop()

st.subheader(f"Öne Çıkan {len(recommendations)} Fon Önerisi")
st.caption("Sıralama: getiri / volatilite oranına göre (yüksek getiri + düşük risk = üstte).")

for rec in recommendations:
    tema_etiket = f" · {rec['tema']}" if rec.get("tema") and rec["tema"] != "Genel / Karma" else ""
    with st.expander(f"**{rec['fonKodu']}** — {rec['fonUnvan']} ({rec['kategori']}{tema_etiket})", expanded=False):
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("1 Hafta", f"%{rec['getiri_1h']:.1f}" if rec['getiri_1h'] == rec['getiri_1h'] else "-")
        m2.metric("1 Ay", f"%{rec['getiri_1a']:.1f}" if rec['getiri_1a'] == rec['getiri_1a'] else "-")
        m3.metric("3 Ay", f"%{rec['getiri_3a']:.1f}" if rec['getiri_3a'] == rec['getiri_3a'] else "-")
        m4.metric("Yıllık Volatilite", f"%{rec['yillik_volatilite_pct']:.1f}" if rec['yillik_volatilite_pct'] == rec['yillik_volatilite_pct'] else "-")
        st.markdown(f"**Neden bu fon?** {rec['gerekce']}")
        if rec["varlik_dagilimi"]:
            _pie(rec["varlik_dagilimi"], "Varlık Dağılımı (%)", key=f"pie_{rec['fonKodu']}")

st.divider()
st.subheader("Tüm Fon Karşılaştırma Tablosu")
display_cols = [
    "fonKodu", "fonUnvan", "kategori", "tema", "getiri_1h", "getiri_1a", "getiri_3a", "getiri_6a",
    "yillik_volatilite_pct", "kategori_persentil_1a",
]
st.dataframe(
    returns_df[display_cols].sort_values("getiri_1a", ascending=False).reset_index(drop=True),
    width="stretch",
    height=400,
    column_config={
        "fonKodu": st.column_config.TextColumn("Fon Kodu", help="TEFAS fon kodu (3 harf)."),
        "fonUnvan": st.column_config.TextColumn("Fon Unvanı", help="Fonun tam adı."),
        "kategori": st.column_config.TextColumn("Kategori", help="TEFAS'ın resmi fon kategorisi (Hisse Senedi, Borçlanma Araçları vb.)."),
        "tema": st.column_config.TextColumn("Tema", help="Fon adından tahmin edilen sektör/tema odağı - resmi TEFAS verisi değildir."),
        "getiri_1h": st.column_config.NumberColumn("1 Hafta %", help="Son 1 haftalık getiri.", format="%.2f%%"),
        "getiri_1a": st.column_config.NumberColumn("1 Ay %", help="Son 1 aylık getiri.", format="%.2f%%"),
        "getiri_3a": st.column_config.NumberColumn("3 Ay %", help="Son 3 aylık getiri.", format="%.2f%%"),
        "getiri_6a": st.column_config.NumberColumn("6 Ay %", help="Son 6 aylık getiri.", format="%.2f%%"),
        "yillik_volatilite_pct": st.column_config.NumberColumn("Yıllık Volatilite %", help="Son 3 aylık günlük getirilerin yıllıklandırılmış standart sapması; risk göstergesidir."),
        "kategori_persentil_1a": st.column_config.NumberColumn("Kategori Persentili", help="Bu fonun 1 aylık getirisinin, aynı kategorideki fonların yüzde kaçından daha iyi olduğu."),
    },
)

st.divider()
st.subheader("Fon Detayı")
selected_fund = st.selectbox("Bir fon kodu seçin", sorted(returns_df["fonKodu"].unique()))
if selected_fund:
    detail = _load_detail(selected_fund, as_of.isoformat())
    hist = detail["tarihce"]
    if not hist.empty:
        fig = px.line(hist, x="tarih", y="fiyat", title=f"{selected_fund} - 12 Aylık NAV Geçmişi", color_discrete_sequence=CHART_COLORS)
        st.plotly_chart(fig, width="stretch")
    if detail["varlik_dagilimi"]:
        _pie(detail["varlik_dagilimi"], f"{selected_fund} - Varlık Dağılımı (%)")
