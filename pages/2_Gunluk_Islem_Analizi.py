"""Gunluk BIST hisse tarama ve gerekceli oneri sayfasi."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import plotly.graph_objects as go
import streamlit as st

from analysis import daily_screener
from data import stock_client

st.set_page_config(page_title="Günlük İşlem Analizi", page_icon="⚡", layout="wide")

st.title("⚡ Günlük İşlem Analizi (Midas — BIST Hisse)")
st.caption(
    "Serbestçe düzenlenebilir bir izleme listesindeki likit BIST hisseleri için teknik tarama. "
    "Bu bir otomatik alım-satım sistemi değildir; sinyaller yalnızca değerlendirme amaçlıdır."
)

col_a, col_b = st.columns([1, 3])
with col_a:
    budget = st.number_input("Günlük İşlem Bütçesi (TL)", min_value=100.0, value=10_000.0, step=500.0)
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
st.dataframe(screening_df, width="stretch", height=400)

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
        ))
        fig.add_trace(go.Scatter(x=hist["tarih"], y=hist["sma20"], name="SMA20", line=dict(width=1)))
        fig.add_trace(go.Scatter(x=hist["tarih"], y=hist["sma50"], name="SMA50", line=dict(width=1)))
        fig.update_layout(title=f"{selected} — 6 Aylık Fiyat Grafiği", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, width="stretch")
