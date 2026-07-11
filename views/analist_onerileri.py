"""Farkli yatirim kuruluslarinin (sell-side analistlerin) al/sat konsensus sayfasi."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data import analyst_client, global_client as gc, stock_client as sc
from ui import gradient_title, recommendation_faq

gradient_title("Analist Önerileri", "🏛️")
st.caption(
    "Farklı yatırım kuruluşlarının (sell-side analistlerin) BIST ve ABD hisseleri için verdiği "
    "al/sat konsensusunu ve ortalama hedef fiyatı gösterir. Kaynak: Yahoo Finance'in topladığı analist "
    "raporları özeti — toplam Güçlü Al/Al/Tut/Sat/Güçlü Sat sayıları Yahoo'nun agregasyonudur (tek tek "
    "hangi bankalar dahil olduğu bu sayılarda belirtilmez), ancak her hissenin altındaki **\"Son Hareket "
    "Eden Kurumlar\"** listesi gerçek kurum adlarını gösterir (ör. Morgan Stanley, JPMorgan, Goldman Sachs "
    "gibi). **Kapsam sınırı:** özellikle küçük/az takip edilen BIST hisselerinde analist kapsaması "
    "olmayabilir; bu durumda hisse tabloda görünmez."
)
st.page_link("views/methodology.py", label="🧭 Kriterlerin tam açıklaması için Nasıl Değerlendiriyoruz? sayfasına gidin", icon="🧭")
recommendation_faq(
    neden=(
        "Bu sayfa kendi teknik taramamızın dışında, gerçek yatırım kuruluşlarının (bankalar, aracı "
        "kurumlar) profesyonel analistlerinin görüşünü tek bir yerde toplar; böylece kendi teknik "
        "sinyallerinizi bağımsız bir profesyonel görüşle karşılaştırabilirsiniz. Analistlerin al/sat "
        "önerisi vermesinin sebebi kendi finansal modelleri, şirket görüşmeleri ve sektör "
        "analizleridir — bizim teknik skorlarımızdan tamamen ayrı bir değerlendirmedir."
    ),
    sure=(
        "Analist hedef fiyatları tipik olarak **12 aylık** bir ufku yansıtır — bu, teknik tarama "
        "sayfalarındaki günlük/haftalık sinyallerden çok daha uzun vadelidir ve genellikle çeyreklik "
        "bilanço dönemlerinde güncellenir. Kısa vadeli alım-satım kararları için tek başına yeterli "
        "değildir."
    ),
)

if st.button("🔄 Verileri Yenile"):
    st.cache_data.clear()
    st.rerun()


@st.cache_data(ttl=3600, show_spinner="Analist verileri toplanıyor (birkaç dakika sürebilir)...")
def _load():
    bist_tickers = {f"{code}.IS": code for code in sc.WATCHLIST}
    us_tickers = {code: code for code in gc.US_WATCHLIST}
    all_map = {**bist_tickers, **us_tickers}
    df = analyst_client.get_recommendations_table(list(all_map.keys()), display_codes=all_map)
    if df.empty:
        return df
    bist_set = set(sc.WATCHLIST)
    df["piyasa"] = df["kod"].map(lambda k: "BIST" if k in bist_set else "ABD")
    return df


try:
    df = _load()
except Exception as exc:
    st.error(f"Analist verisi çekilirken hata oluştu: {exc}")
    st.stop()

if df.empty:
    st.info("Analist kapsaması bulunan hisse bulunamadı, lütfen tekrar deneyin.")
    st.stop()

market_filter = st.radio("Piyasa", ["Tümü", "BIST", "ABD"], horizontal=True)
view_df = df if market_filter == "Tümü" else df[df["piyasa"] == market_filter]

firm_counts: dict[str, int] = {}
for moves in view_df["son_hareketler"]:
    for m in moves or []:
        firma = m.get("firma")
        if firma:
            firm_counts[firma] = firm_counts.get(firma, 0) + 1

st.subheader("Hangi Kurumlar Takip Ediyor?")
st.caption(
    "Aşağıdaki liste, seçili piyasadaki hisselerin \"Son Hareket Eden Kurumlar\" verisinde en az bir kez "
    "geçen yatırım kuruluşlarını (bankalar, aracı kurumlar) ve kaç hissede hareket ettiklerini gösterir. "
    "Bir veya birden fazla kurum seçerek sayfayı sadece o kurum(lar)ın yakın zamanda görüş bildirdiği "
    "hisselerle sınırlayabilirsiniz."
)
if firm_counts:
    firm_df = (
        pd.DataFrame(sorted(firm_counts.items(), key=lambda kv: kv[1], reverse=True), columns=["Kurum", "Hisse Sayısı"])
    )
    c1, c2 = st.columns([2, 3])
    with c1:
        st.dataframe(firm_df, width="stretch", height=280, hide_index=True)
    with c2:
        selected_firms = st.multiselect(
            "Kuruma göre filtrele", options=firm_df["Kurum"].tolist(), placeholder="Kurum seçin"
        )
    if selected_firms:
        mask = view_df["son_hareketler"].apply(
            lambda moves: any((m.get("firma") in selected_firms) for m in (moves or []))
        )
        view_df = view_df[mask]
        if view_df.empty:
            st.info("Seçilen kurum(lar) için yakın zamanda hareket eden hisse bulunamadı.")
            st.stop()
else:
    st.info("Bu piyasada kurum bazlı hareket verisi bulunamadı.")

st.divider()
st.subheader("En Güçlü Konsensuslar (Al Yönlü)")
top = view_df.sort_values("konsensus_skor", ascending=True, na_position="last").head(5)
for _, row in top.iterrows():
    with st.expander(f"**{row['kod']}** ({row['piyasa']}) — {row['konsensus'].replace('_', ' ').title()}", expanded=False):
        m1, m2, m3 = st.columns(3)
        m1.metric("Analist Sayısı", f"{int(row['toplam_analist'])}")
        m2.metric("Ortalama Hedef Fiyat", f"{row['hedef_fiyat_ort']:.2f}" if pd.notna(row['hedef_fiyat_ort']) else "-")
        m3.metric("Hedefe Göre Potansiyel", f"%{row['hedef_getiri_pct']:.1f}" if pd.notna(row['hedef_getiri_pct']) else "-")
        st.markdown(
            f"Dağılım: 🟢 Güçlü Al **{int(row['guclu_al'])}** · Al **{int(row['al'])}** · "
            f"Tut **{int(row['tut'])}** · Sat **{int(row['sat'])}** · 🔴 Güçlü Sat **{int(row['guclu_sat'])}**"
        )
        st.markdown(row.get("gerekce", ""))
        st.markdown(row.get("kendi_onerimiz", ""))
        st.markdown(f"**Ne kadar süre için geçerli?** {row.get('tutma_suresi', '')}")
        moves = row.get("son_hareketler") or []
        if moves:
            st.markdown("**Son Hareket Eden Kurumlar:**")
            for m in moves[:8]:
                tarih = pd.to_datetime(m["tarih"], unit="s").date().isoformat() if m.get("tarih") else "-"
                aksiyon = {"up": "Yükseltti", "down": "Düşürdü", "main": "Korudu", "reit": "Yineledi", "init": "Kapsama Aldı"}.get(m.get("aksiyon"), m.get("aksiyon", "-"))
                st.caption(f"{tarih} · **{m['firma']}** — {aksiyon} → {m.get('yeni_derece', '-')} (hedef: {m.get('hedef_fiyat', '-')})")

st.divider()
st.subheader("Analist Dağılım Grafiği")
chart_df = view_df.sort_values("konsensus_skor", ascending=True, na_position="last").head(15)
fig = go.Figure()
fig.add_trace(go.Bar(name="Güçlü Al", x=chart_df["kod"], y=chart_df["guclu_al"], marker_color="#008300"))
fig.add_trace(go.Bar(name="Al", x=chart_df["kod"], y=chart_df["al"], marker_color="#1baf7a"))
fig.add_trace(go.Bar(name="Tut", x=chart_df["kod"], y=chart_df["tut"], marker_color="#eda100"))
fig.add_trace(go.Bar(name="Sat", x=chart_df["kod"], y=chart_df["sat"], marker_color="#e87ba4"))
fig.add_trace(go.Bar(name="Güçlü Sat", x=chart_df["kod"], y=chart_df["guclu_sat"], marker_color="#e34948"))
fig.update_layout(barmode="stack", title="Analist Öneri Dağılımı (en güçlü konsensuslar)")
st.plotly_chart(fig, width="stretch")

st.divider()
st.subheader("Tüm Tablo")
ozet = view_df.rename(columns={
    "kod": "Kod", "piyasa": "Piyasa", "guclu_al": "Güçlü Al", "al": "Al", "tut": "Tut", "sat": "Sat",
    "guclu_sat": "Güçlü Sat", "toplam_analist": "Analist Sayısı", "konsensus": "Konsensus",
    "konsensus_skor": "Konsensus Skoru", "guncel_fiyat": "Güncel Fiyat", "hedef_fiyat_ort": "Hedef Fiyat (Ort.)",
    "hedef_fiyat_yuksek": "Hedef Fiyat (En Yüksek)", "hedef_fiyat_dusuk": "Hedef Fiyat (En Düşük)",
    "hedef_getiri_pct": "Hedefe Göre Potansiyel %",
})
st.dataframe(
    ozet,
    width="stretch",
    height=450,
    column_config={
        "Konsensus Skoru": st.column_config.NumberColumn(help="1.0 = Güçlü Al, 3.0 = Tut, 5.0 = Güçlü Sat (analist ortalaması). Düşük = daha olumlu."),
        "Hedefe Göre Potansiyel %": st.column_config.NumberColumn(help="Analistlerin ortalama hedef fiyatının güncel fiyata göre yüzde farkı.", format="%.1f%%"),
        "Analist Sayısı": st.column_config.NumberColumn(help="Bu hisseyi takip eden/görüş bildiren analist sayısı."),
    },
)
