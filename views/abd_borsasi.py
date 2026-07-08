"""ABD borsasi (S&P500/Nasdaq/Dow bilesenleri) teknik tarama sayfasi - BIST sayfasiyla ayni kriterler."""
import plotly.graph_objects as go
import streamlit as st

from analysis import daily_screener
from data import global_client as gc
from ui import gradient_title

gradient_title("ABD Borsası", "🇺🇸")
st.caption(
    "Büyük/likit ABD hisseleri için Günlük İşlem Analizi sayfasıyla **birebir aynı** teknik tarama "
    "formülü (trend + RSI + hacim + momentum) kullanılır; tek fark evrenin ABD hisseleri olması ve "
    "fiyatların USD cinsinden olmasıdır."
)
st.page_link("views/methodology.py", label="🧭 Kriterlerin tam açıklaması için Nasıl Değerlendiriyoruz? sayfasına gidin", icon="🧭")

col_a, col_b = st.columns([1, 3])
with col_a:
    budget = st.number_input("İşlem Bütçesi (USD)", min_value=10.0, value=1_000.0, step=100.0)
    if st.button("🔄 Verileri Yenile"):
        st.cache_data.clear()
        st.rerun()


@st.cache_data(ttl=900, show_spinner="ABD hisseleri taranıyor...")
def _load_screening(budget_usd: float):
    return daily_screener.build_us_screening(budget_usd=budget_usd)


@st.cache_data(ttl=900, show_spinner="Endeks verisi yükleniyor...")
def _load_indices():
    out = {}
    for ticker, ad in gc.US_INDICES.items():
        try:
            hist = gc.get_us_history(ticker, range_="6mo", interval="1d")
            if not hist.empty:
                out[ad] = hist
        except Exception:
            continue
    return out


@st.cache_data(ttl=900, show_spinner="Hisse verisi yükleniyor...")
def _load_history(ticker: str):
    return gc.get_us_history(ticker, range_="6mo", interval="1d")


try:
    screening_df = _load_screening(float(budget))
except Exception as exc:
    st.error(f"ABD borsası verisi çekilirken hata oluştu: {exc}")
    st.stop()

if screening_df.empty:
    st.info("Veri çekilemedi, lütfen tekrar deneyin.")
    st.stop()

screening_df["sektor"] = screening_df["kod"].map(gc.US_SECTORS).fillna("Diğer")

st.subheader("Ana Endeksler")
indices = _load_indices()
if indices:
    idx_cols = st.columns(len(indices))
    for col, (ad, hist) in zip(idx_cols, indices.items()):
        last = hist.iloc[-1]
        col.metric(ad, f"{last['kapanis']:,.2f}", delta=f"%{last['gunluk_getiri_pct']:.2f}" if last['gunluk_getiri_pct'] == last['gunluk_getiri_pct'] else None)

st.divider()
st.subheader("Bugünün Öne Çıkan Adayları")
top_picks = screening_df.head(5)
for _, row in top_picks.iterrows():
    with st.expander(f"**{row['kod']}** · {row['sektor']} — {row['fiyat']:.2f} USD (Skor: {row['skor']:.1f})", expanded=False):
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Günlük Değişim", f"%{row['gunluk_getiri_pct']:.2f}" if row['gunluk_getiri_pct'] == row['gunluk_getiri_pct'] else "-")
        m2.metric("RSI(14)", f"{row['rsi14']:.0f}" if row['rsi14'] == row['rsi14'] else "-")
        m3.metric("Hacim Oranı (20g ort.)", f"{row['hacim_orani']:.2f}x" if row['hacim_orani'] == row['hacim_orani'] else "-")
        m4.metric(f"{budget:,.0f} USD ile alınabilir", f"{int(row['alinabilecek_adet'])} adet")
        st.markdown(f"**Neden bu hisse?** {row['gerekce']}")

st.divider()
st.subheader("Tüm İzleme Listesi")
st.dataframe(
    screening_df,
    width="stretch",
    height=400,
    column_config={
        "kod": st.column_config.TextColumn("Kod", help="ABD borsa sembolü (Yahoo Finance)."),
        "fiyat": st.column_config.NumberColumn("Fiyat (USD)", help="Güncel/son kapanış fiyatı, USD."),
        "gunluk_getiri_pct": st.column_config.NumberColumn("Günlük Değişim %", help="Bir önceki kapanışa göre yüzde değişim.", format="%.2f%%"),
        "rsi14": st.column_config.NumberColumn("RSI(14)", help="14 günlük Göreceli Güç Endeksi: 70 üzeri aşırı alım, 30 altı aşırı satım."),
        "sma20_uzerinde": st.column_config.CheckboxColumn("SMA20 Üzerinde mi?", help="Fiyat, 20 ve 50 günlük ortalamaların üzerinde ve kısa vadeli trend yukarı yönlü mü?"),
        "hacim_orani": st.column_config.NumberColumn("Hacim Oranı", help="Günlük hacmin, son 20 günlük ortalama hacme oranı (>1.3x = ilgi artışı)."),
        "momentum_5g_pct": st.column_config.NumberColumn("5G Momentum %", help="Son 5 işlem gününe göre kümülatif getiri.", format="%.2f%%"),
        "skor": st.column_config.NumberColumn("Skor", help="Trend + RSI + hacim + momentum bileşenlerinin ağırlıklı toplamı; sıralama bu skora göre yapılır."),
        "alinabilecek_adet": st.column_config.NumberColumn("Alınabilecek Adet", help="Girilen bütçeyle bu fiyattan alınabilecek tam adet sayısı."),
        "sektor": st.column_config.TextColumn("Sektör", help="Elle hazırlanmış sabit sektör haritasından gelir (resmi borsa verisi değildir)."),
        "gerekce": st.column_config.TextColumn("Gerekçe", help="Skoru oluşturan sinyallerin okunabilir açıklaması."),
    },
)

st.divider()
st.subheader("Hisse Detayı")
selected = st.selectbox("Bir hisse seçin", screening_df["kod"].tolist())
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
        st.plotly_chart(fig, width="stretch")
