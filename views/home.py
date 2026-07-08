"""Ana sayfa - genel bakis, parametrik butceler ve one cikan enstrumanlar."""
import datetime as dt

import streamlit as st

from analysis import daily_screener, fund_analysis
from data import global_client as gc
from portfolio import db
from ui import gradient_title

db.init_db()

gradient_title("Fon & BIST/ABD Hisse Analiz Sistemi", "📊")
st.markdown(
    """
Bu panel yatırım döngüleriniz için analiz ve öneri üretir; ayrıca ABD borsasını, döviz/kıymetli maden
fiyatlarını ve farklı yatırım kuruluşlarının analist önerilerini tek yerden takip etmenizi sağlar.

- **📈 Haftalık Fon Analizi** — TEFAS fon karşılaştırması, varlık dağılımı ve gerekçeli öneriler.
- **⚡ Günlük İşlem Analizi** — BIST hisse teknik taraması ve gerekçeli öneriler.
- **🇺🇸 ABD Borsası** — aynı teknik kriterlerle ABD hisse taraması.
- **💱 Döviz & Kıymetli Maden** — Dolar/Euro/Sterlin ve altın/gümüş yön okuması.
- **🏛️ Analist Önerileri** — farklı yatırım kuruluşlarının al/sat konsensusu.
- **🌂 Şemsiye Portföy Oluşturucu** — sektör hedeflerinize göre fon/hisse portföyü.
- **🏆 Sektörel Performans** — hangi sektörler/temalar öne çıkıyor.
- **💼 Portföyüm** — nakit bakiye, pozisyonlar, işlem geçmişi.

Sol menüden bir sayfa seçin; her sayfada **"🔄 Verileri Yenile"** butonuyla güncel veri çekebilirsiniz.
"""
)
st.page_link(
    "views/methodology.py",
    label="🧭 Tüm sayfalardaki kriterlerin tam açıklaması: Nasıl Değerlendiriyoruz?",
    icon="🧭",
)

st.divider()
st.subheader("💰 Yatırım Bütçelerim")
st.caption(
    "Bu tutarlar Portföyüm sayfasındaki nakit bakiyenizle aynıdır ve diğer sayfalardaki (Şemsiye Portföy "
    "Oluşturucu vb.) varsayılan bütçe olarak kullanılır. İstediğiniz zaman güncelleyebilirsiniz."
)
col1, col2 = st.columns(2)
with col1:
    fund_budget_input = st.number_input(
        "Haftalık Fon Bütçesi (TL)", min_value=0.0, value=float(db.get_balance("FUND")), step=1_000.0
    )
    if st.button("Fon Bütçesini Güncelle"):
        db.set_balance("FUND", fund_budget_input)
        st.success("Fon bütçesi güncellendi.")
        st.rerun()
with col2:
    daily_budget_input = st.number_input(
        "Günlük İşlem Bütçesi (TL)", min_value=0.0, value=float(db.get_balance("DAILY")), step=500.0
    )
    if st.button("Hisse Bütçesini Güncelle"):
        db.set_balance("DAILY", daily_budget_input)
        st.success("Hisse bütçesi güncellendi.")
        st.rerun()

st.divider()
col_h, col_r = st.columns([3, 1])
with col_h:
    st.subheader("⭐ Öne Çıkanlar")
    st.caption(
        "Her kategori, kendi sayfasındaki skorlama kriterine göre öne çıkan ilk 3 adaydır — "
        "tam kriter listesi için yukarıdaki **Nasıl Değerlendiriyoruz?** bağlantısına bakın."
    )
with col_r:
    st.write("")
    if st.button("🔄 Öne Çıkanları Yenile"):
        st.cache_data.clear()
        st.rerun()


@st.cache_data(ttl=3600, show_spinner="Fon evreni çekiliyor (birkaç dakika sürebilir)...")
def _top_funds(as_of_str: str):
    as_of = dt.date.fromisoformat(as_of_str)
    _, recs = fund_analysis.build_fund_comparison(top_n=3, as_of=as_of)
    return recs


@st.cache_data(ttl=900, show_spinner="BIST hisseleri taranıyor...")
def _top_bist():
    df = daily_screener.build_daily_screening()
    return df.head(3) if not df.empty else df


@st.cache_data(ttl=900, show_spinner="ABD hisseleri taranıyor...")
def _top_us():
    df = daily_screener.build_us_screening()
    return df.head(3) if not df.empty else df


@st.cache_data(ttl=900, show_spinner="Döviz/kıymetli maden verisi çekiliyor...")
def _fx_metals():
    return gc.build_fx_metals_table()


tab_fund, tab_bist, tab_us, tab_fx = st.tabs(
    ["📈 Fonlar", "⚡ BIST Hisseleri", "🇺🇸 ABD Hisseleri", "💱 Döviz / Altın"]
)

with tab_fund:
    try:
        recs = _top_funds(dt.date.today().isoformat())
    except Exception as exc:
        st.error(f"Fon verisi çekilirken hata oluştu: {exc}")
        recs = []
    if not recs:
        st.info("Fon verisi çekilemedi, lütfen yenileyin.")
    for rec in recs:
        with st.expander(f"**{rec['fonKodu']}** — {rec['fonUnvan']}", expanded=False):
            m1, m2, m3 = st.columns(3)
            m1.metric("1 Ay Getiri", f"%{rec['getiri_1a']:.1f}" if rec['getiri_1a'] == rec['getiri_1a'] else "-")
            m2.metric("3 Ay Getiri", f"%{rec['getiri_3a']:.1f}" if rec['getiri_3a'] == rec['getiri_3a'] else "-")
            m3.metric("Yıllık Volatilite", f"%{rec['yillik_volatilite_pct']:.1f}" if rec['yillik_volatilite_pct'] == rec['yillik_volatilite_pct'] else "-")
            st.markdown(f"**Neden bu fon?** {rec['gerekce']}")
    st.page_link("views/weekly_fund.py", label="Tüm fon karşılaştırma tablosuna git →", icon="📈")

with tab_bist:
    try:
        top_bist = _top_bist()
    except Exception as exc:
        st.error(f"BIST verisi çekilirken hata oluştu: {exc}")
        top_bist = None
    if top_bist is None or top_bist.empty:
        st.info("BIST verisi çekilemedi, lütfen yenileyin.")
    else:
        for _, row in top_bist.iterrows():
            with st.expander(f"**{row['kod']}** — {row['fiyat']:.2f} TL (Skor: {row['skor']:.1f})", expanded=False):
                m1, m2 = st.columns(2)
                m1.metric("Günlük Değişim", f"%{row['gunluk_getiri_pct']:.2f}" if row['gunluk_getiri_pct'] == row['gunluk_getiri_pct'] else "-")
                m2.metric("RSI(14)", f"{row['rsi14']:.0f}" if row['rsi14'] == row['rsi14'] else "-")
                st.markdown(f"**Neden bu hisse?** {row['gerekce']}")
    st.page_link("views/daily_stock.py", label="Tüm BIST izleme listesine git →", icon="⚡")

with tab_us:
    try:
        top_us = _top_us()
    except Exception as exc:
        st.error(f"ABD borsası verisi çekilirken hata oluştu: {exc}")
        top_us = None
    if top_us is None or top_us.empty:
        st.info("ABD borsası verisi çekilemedi, lütfen yenileyin.")
    else:
        for _, row in top_us.iterrows():
            with st.expander(f"**{row['kod']}** — {row['fiyat']:.2f} USD (Skor: {row['skor']:.1f})", expanded=False):
                m1, m2 = st.columns(2)
                m1.metric("Günlük Değişim", f"%{row['gunluk_getiri_pct']:.2f}" if row['gunluk_getiri_pct'] == row['gunluk_getiri_pct'] else "-")
                m2.metric("RSI(14)", f"{row['rsi14']:.0f}" if row['rsi14'] == row['rsi14'] else "-")
                st.markdown(f"**Neden bu hisse?** {row['gerekce']}")
    st.page_link("views/abd_borsasi.py", label="Tüm ABD izleme listesine git →", icon="🇺🇸")

with tab_fx:
    try:
        fx_df = _fx_metals()
    except Exception as exc:
        st.error(f"Döviz/kıymetli maden verisi çekilirken hata oluştu: {exc}")
        fx_df = None
    if fx_df is None or fx_df.empty:
        st.info("Veri çekilemedi, lütfen yenileyin.")
    else:
        cols = st.columns(len(fx_df))
        for col, (_, row) in zip(cols, fx_df.iterrows()):
            with col:
                birim = row["birim"]
                deger = f"{row['fiyat']:.4f}" if birim == "TL" else f"{row['fiyat']:.2f}"
                col.metric(row["ad"], f"{deger} {birim}", delta=f"%{row['gunluk_getiri_pct']:.2f}" if row['gunluk_getiri_pct'] == row['gunluk_getiri_pct'] else None)
                st.caption(row["sinyal"])
    st.page_link("views/doviz_kiymetli_maden.py", label="Detaylı döviz/kıymetli maden sayfasına git →", icon="💱")

st.divider()
col1, col2 = st.columns(2)
with col1:
    st.metric("Haftalık Fon Kasası - Nakit Bakiye", f"{db.get_balance('FUND'):,.2f} TL")
with col2:
    st.metric("Günlük İşlem Kasası - Nakit Bakiye", f"{db.get_balance('DAILY'):,.2f} TL")
