"""Gunluk BIST hisse tarama ve gerekceli oneri sayfasi."""
import plotly.graph_objects as go
import streamlit as st

from analysis import daily_screener
from data import stock_client
from portfolio import db
from ui import gradient_title, recommendation_faq

gradient_title("Günlük İşlem Analizi (Midas — BIST Hisse)", "⚡")
st.caption("Serbestçe düzenlenebilir bir izleme listesindeki likit BIST hisseleri için teknik tarama.")
st.page_link("views/methodology.py", label="🧭 Kriterlerin tam açıklaması için Nasıl Değerlendiriyoruz? sayfasına gidin", icon="🧭")
recommendation_faq(
    neden=(
        "Yüzlerce BIST hissesini tek tek incelemek yerine, bu sayfa sabit ve şeffaf kriterlere "
        "(trend, RSI, hacim, momentum) dayalı bir puanlama ile 'bugün hangi hisseye bakmalıyım' "
        "sorusuna hızlı bir başlangıç noktası sunar. Bu bir kesin alım-satım emri değildir — "
        "dikkatinizi nereye yönlendireceğinize dair bir öneridir, nihai karar ve araştırma "
        "sorumluluğu size aittir."
    ),
    sure=(
        "Kısa vadelidir: RSI, hacim ve momentum gibi bileşenler gün içinde hızla değişebileceğinden "
        "sinyal tipik olarak birkaç gün ile 2-3 hafta arasında anlamlıdır. Sayfayı düzenli (idealde "
        "her gün) yenileyerek güncel tutun; şirket haberleri/bilanço gibi temel gelişmeler bu skora "
        "dahil değildir."
    ),
)

budget = db.get_balance("DAILY")
col_a, col_b = st.columns([1, 3])
with col_a:
    st.metric("Günlük İşlem Bütçesi (TL)", f"{budget:,.2f}")
    st.caption("Portföyüm sayfasındaki Günlük İşlem Kasası bakiyeniz; oradan güncelleyebilirsiniz.")
    if st.button("🔄 Verileri Yenile"):
        st.cache_data.clear()
        st.rerun()


@st.cache_data(ttl=900, show_spinner="BIST hisseleri taranıyor...")
def _load_screening(budget_tl: float):
    return daily_screener.build_daily_screening(budget_tl=budget_tl)


@st.cache_data(ttl=900, show_spinner="Hisse verisi yükleniyor...")
def _load_history(code: str):
    return stock_client.get_stock_history(code, range_="6mo", interval="1d")


try:
    screening_df = _load_screening(float(budget))
except Exception as exc:
    st.error(f"BIST verisi çekilirken hata oluştu: {exc}")
    st.stop()

if screening_df.empty:
    st.info("Veri çekilemedi, lütfen tekrar deneyin.")
    st.stop()

st.subheader("Bugünün Öne Çıkan Adayları")
top_picks = screening_df.head(5)
for _, row in top_picks.iterrows():
    with st.expander(f"**{row['kod']}** — {row['fiyat']:.2f} TL (Skor: {row['skor']:.1f})", expanded=False):
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Günlük Değişim", f"%{row['gunluk_getiri_pct']:.2f}" if row['gunluk_getiri_pct'] == row['gunluk_getiri_pct'] else "-")
        m2.metric("RSI(14)", f"{row['rsi14']:.0f}" if row['rsi14'] == row['rsi14'] else "-")
        m3.metric("Hacim Oranı (20g ort.)", f"{row['hacim_orani']:.2f}x" if row['hacim_orani'] == row['hacim_orani'] else "-")
        m4.metric(f"{budget:,.0f} TL ile alınabilir", f"{int(row['alinabilecek_adet'])} adet")
        st.markdown(f"**Neden bu hisse?** {row['gerekce']}")

st.divider()
st.subheader("Tüm İzleme Listesi")
st.dataframe(
    screening_df,
    use_container_width=True,
    height=400,
    column_config={
        "kod": st.column_config.TextColumn("Kod", help="BIST hisse kodu."),
        "fiyat": st.column_config.NumberColumn("Fiyat (TL)", help="Güncel/son kapanış fiyatı."),
        "gunluk_getiri_pct": st.column_config.NumberColumn("Günlük Değişim %", help="Bir önceki kapanışa göre yüzde değişim.", format="%.2f%%"),
        "rsi14": st.column_config.NumberColumn("RSI(14)", help="14 günlük Göreceli Güç Endeksi: 70 üzeri aşırı alım, 30 altı aşırı satım."),
        "sma20_uzerinde": st.column_config.CheckboxColumn("SMA20 Üzerinde mi?", help="Fiyat, 20 ve 50 günlük ortalamaların üzerinde ve kısa vadeli trend yukarı yönlü mü?"),
        "hacim_orani": st.column_config.NumberColumn("Hacim Oranı", help="Günlük hacmin, son 20 günlük ortalama hacme oranı (>1.3x = ilgi artışı)."),
        "momentum_5g_pct": st.column_config.NumberColumn("5G Momentum %", help="Son 5 işlem gününe göre kümülatif getiri.", format="%.2f%%"),
        "skor": st.column_config.NumberColumn("Skor", help="Trend + RSI + hacim + momentum bileşenlerinin ağırlıklı toplamı; sıralama bu skora göre yapılır."),
        "alinabilecek_adet": st.column_config.NumberColumn("Alınabilecek Adet", help="Girilen bütçeyle bu fiyattan alınabilecek tam adet sayısı."),
        "gerekce": st.column_config.TextColumn("Gerekçe", help="Skoru oluşturan sinyallerin okunabilir açıklaması."),
    },
)

st.divider()
st.subheader("Hisse Detayı")
selected = st.selectbox("Bir hisse kodu seçin", screening_df["kod"].tolist())
if selected:
    hist = _load_history(selected)
    if not hist.empty:
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=hist["tarih"], open=hist["acilis"], high=hist["yuksek"], low=hist["dusuk"], close=hist["kapanis"],
            name=selected,
            increasing_line_color="#1baf7a", decreasing_line_color="#e34948",
        ))
        fig.add_trace(go.Scatter(x=hist["tarih"], y=hist["sma20"], name="SMA20", line=dict(width=1.5, color="#4a3aa7")))
        fig.add_trace(go.Scatter(x=hist["tarih"], y=hist["sma50"], name="SMA50", line=dict(width=1.5, color="#eb6834")))
        fig.update_layout(title=f"{selected} — 6 Aylık Fiyat Grafiği", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
        with st.expander("🕯️ Bu mum (candlestick) grafiği nasıl okunur?"):
            st.markdown(
                """
Her mum bir işlem gününü temsil eder ve o günün **açılış, kapanış, en yüksek ve en düşük** fiyatını gösterir:

- **Gövde (kalın dikdörtgen kısım):** açılış ile kapanış fiyatı arasındaki aralıktır.
- **Fitil (gövdenin üst/altındaki ince çizgiler):** o gün içinde görülen en yüksek ve en düşük fiyatı gösterir.
- **🟢 Yeşil mum:** kapanış fiyatı açılıştan **yüksek** — gün yükselişle kapanmış (gövdenin altı = açılış, üstü = kapanış).
- **🔴 Kırmızı mum:** kapanış fiyatı açılıştan **düşük** — gün düşüşle kapanmış (gövdenin üstü = açılış, altı = kapanış).
- **Mor çizgi (SMA20) / turuncu çizgi (SMA50):** son 20 / 50 günün ortalama kapanış fiyatı — kısa vadeli trendi gösterir.
  Mumlar bu çizgilerin üzerindeyse fiyat kısa vadeli ortalamasının üzerinde seyrediyor demektir.
"""
            )
