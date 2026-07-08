"""Doviz paritesi + kiymetli maden (altin/gumus) takip sayfasi."""
import plotly.graph_objects as go
import streamlit as st

from data import global_client as gc
from ui import gradient_title

gradient_title("Döviz & Kıymetli Maden", "💱")
st.caption(
    "Dolar/Euro/Sterlin paritelerini ve ons bazlı altın/gümüş fiyatlarını (gram altın TL karşılığıyla "
    "birlikte) aynı teknik kriterlerle (trend + RSI + momentum) izler ve yön (Al/Sat/Nötr) okuması sunar. "
    "**Tek bir kaynağa dayanmaz:** birincil kaynak Yahoo Finance'in teknik göstergeleridir; buna ek olarak "
    "dövizde Frankfurter.app/Avrupa Merkez Bankası referans kuru, kıymetli madende ise GLD/SLV ETF fiyat "
    "hareketi bağımsız bir ikinci kaynak olarak çapraz kontrol edilir. Veriler 15 dakikada bir güncellenir."
)
st.page_link("views/methodology.py", label="🧭 Kriterlerin tam açıklaması için Nasıl Değerlendiriyoruz? sayfasına gidin", icon="🧭")

if st.button("🔄 Verileri Yenile"):
    st.cache_data.clear()
    st.rerun()


@st.cache_data(ttl=900, show_spinner="Döviz ve kıymetli maden verisi çekiliyor...")
def _load():
    return gc.build_fx_metals_table()


try:
    df = _load()
except Exception as exc:
    st.error(f"Veri çekilirken hata oluştu: {exc}")
    st.stop()

if df.empty:
    st.info("Veri çekilemedi, lütfen tekrar deneyin.")
    st.stop()

st.subheader("Anlık Tablo")
cols = st.columns(len(df))
for col, (_, row) in zip(cols, df.iterrows()):
    with col:
        birim = row["birim"]
        deger = f"{row['fiyat']:.4f}" if birim == "TL" else f"{row['fiyat']:.2f}"
        st.metric(
            f"{row['ad']}",
            f"{deger} {birim}",
            delta=f"%{row['gunluk_getiri_pct']:.2f}" if row['gunluk_getiri_pct'] == row['gunluk_getiri_pct'] else None,
        )
        if row["birim"] != "TL" and row.get("gram_try") == row.get("gram_try") and row.get("gram_try"):
            st.caption(f"Gram karşılığı: ≈ {row['gram_try']:,.2f} TL")

st.divider()
st.subheader("Yön Okuması ve Gerekçe")
for _, row in df.iterrows():
    renk = "🟢" if row["sinyal"] == "Al Yönlü" else ("🔴" if row["sinyal"] == "Sat Yönlü" else "⚪")
    with st.expander(f"{renk} **{row['ad']}** — {row['sinyal']}", expanded=False):
        m1, m2, m3 = st.columns(3)
        m1.metric("5 Gün Momentum", f"%{row['momentum_5g_pct']:.2f}")
        m2.metric("RSI(14)", f"{row['rsi14']:.0f}" if row['rsi14'] == row['rsi14'] else "-")
        m3.metric("Günlük Değişim", f"%{row['gunluk_getiri_pct']:.2f}" if row['gunluk_getiri_pct'] == row['gunluk_getiri_pct'] else "-")
        st.caption(f"İkincil kaynak: {row['ikincil_kaynak']}")
        st.markdown(row["gerekce"])
        st.markdown(row["kendi_onerimiz"])
        st.markdown(f"**Ne kadar süre tutulmalı?** {row['tutma_suresi']}")

st.divider()
st.subheader("Tüm Tablo")
ozet = df[["kod", "ad", "birim", "fiyat", "gunluk_getiri_pct", "momentum_5g_pct", "rsi14", "sinyal", "ikincil_kaynak", "gram_try"]].rename(columns={
    "kod": "Kod", "ad": "Ad", "birim": "Birim", "fiyat": "Fiyat",
    "gunluk_getiri_pct": "Günlük Değişim %", "momentum_5g_pct": "5G Momentum %",
    "rsi14": "RSI(14)", "sinyal": "Sinyal", "ikincil_kaynak": "İkincil Kaynak", "gram_try": "Gram (TL)",
})
st.dataframe(
    ozet,
    width="stretch",
    column_config={
        "Fiyat": st.column_config.NumberColumn(help="Birim sütununda belirtilen para biriminden anlık fiyat."),
        "Günlük Değişim %": st.column_config.NumberColumn(help="Bir önceki kapanışa göre günlük yüzde değişim.", format="%.2f%%"),
        "5G Momentum %": st.column_config.NumberColumn(help="Son 5 işlem gününe göre kümülatif getiri.", format="%.2f%%"),
        "RSI(14)": st.column_config.NumberColumn(help="14 günlük Göreceli Güç Endeksi: 70 üzeri aşırı alım, 30 altı aşırı satım bölgesi."),
        "Sinyal": st.column_config.TextColumn(help="Birincil (Yahoo teknik) + ikincil kaynağın birleşik okuması; kesin alım-satım talimatı değildir."),
        "İkincil Kaynak": st.column_config.TextColumn(help="Yön okumasını teyit/çürütmek için kullanılan bağımsız ikinci veri kaynağı."),
        "Gram (TL)": st.column_config.NumberColumn(help="Ons fiyatının gram karşılığının güncel Dolar/TL kuruyla çarpılmış hali (yalnızca altın/gümüş satırları için)."),
    },
)

st.divider()
st.subheader("Fiyat Grafiği")
secim = st.selectbox("Enstrüman seçin", df["ad"].tolist())
if secim:
    ticker_map = {**{v: k for k, v in gc.FX_PAIRS.items()}, **{v: k for k, v in gc.METAL_FUTURES.items()}}
    ticker = ticker_map.get(secim)
    if ticker:
        hist = gc.get_us_history(ticker, range_="6mo", interval="1d")
        if not hist.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=hist["tarih"], y=hist["kapanis"], name=secim, line=dict(width=2, color="#2563EB")))
            fig.add_trace(go.Scatter(x=hist["tarih"], y=hist["sma20"], name="SMA20", line=dict(width=1.5, color="#eda100")))
            fig.add_trace(go.Scatter(x=hist["tarih"], y=hist["sma50"], name="SMA50", line=dict(width=1.5, color="#e34948")))
            fig.update_layout(title=f"{secim} — 6 Aylık Fiyat Grafiği")
            st.plotly_chart(fig, width="stretch")
