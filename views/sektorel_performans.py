"""Fon temalarinin ve hisse sektorlerinin performans siralamasi (anlik goruntu)."""
import datetime as dt

import plotly.express as px
import streamlit as st

from analysis import daily_screener, umbrella
from data import tefas_client
from ui import CHART_COLORS, gradient_title

gradient_title("Sektörel Performans", "🏆")
st.caption(
    "Fon temaları ve hisse sektörleri, sistemin mevcut performans parametreleriyle ayrı ayrı sıralanır: "
    "fonlar için güvenilirlik filtresini geçen fonların **ortalama 1 ay / 3 ay getirisi**, hisseler için "
    "izleme listesindeki hisselerin **ortalama teknik skoru ve 5 günlük momentumu**. "
    "**Önemli sınır:** fon tema etiketi fon adından tahmindir, hisse sektör etiketi elle hazırlanmış sabit "
    "bir haritadan gelir. Bu sayfa **bu an itibariyle** bir anlık görüntüdür (snapshot); **🔄 Verileri "
    "Yenile** ile güncellenebilir. Detaylar için **🧭 Nasıl Değerlendiriyoruz?** sayfasına bakabilirsiniz."
)

if st.button("🔄 Verileri Yenile"):
    st.cache_data.clear()
    st.rerun()


@st.cache_data(ttl=3600, show_spinner="TEFAS'tan fon evreni çekiliyor (birkaç dakika sürebilir)...")
def _load_funds(as_of_str: str):
    return tefas_client.get_universe_returns(dt.date.fromisoformat(as_of_str))


@st.cache_data(ttl=900, show_spinner="BIST hisseleri taranıyor...")
def _load_stocks():
    return daily_screener.build_daily_screening()


as_of = dt.date.today()
try:
    funds_df = _load_funds(as_of.isoformat())
    stocks_df = _load_stocks()
except Exception as exc:
    st.error(f"Veri çekilirken hata oluştu: {exc}")
    st.stop()

# ---------------- Fon temalari ----------------
st.subheader("📈 Fon Temaları Sıralaması")
tema_perf = umbrella.fund_theme_performance(funds_df)
if tema_perf.empty:
    st.info("Fon verisi çekilemedi, lütfen verileri yenileyin.")
else:
    chart_df = tema_perf.sort_values("ort_skor", ascending=True)
    fig = px.bar(
        chart_df,
        x="ort_skor",
        y="tema",
        orientation="h",
        title="Fon Temaları — Ortalama Getiri Skoru (1a/3a/6a ortalaması, %)",
        labels={"ort_skor": "Ortalama getiri skoru (%)", "tema": ""},
        color_discrete_sequence=[CHART_COLORS[0]],
    )
    fig.update_layout(height=max(400, 28 * len(chart_df)))
    st.plotly_chart(fig, width="stretch")

    tema_tablo = tema_perf.rename(
        columns={
            "tema": "Tema",
            "fon_sayisi": "Fon Sayısı",
            "ort_getiri_1a": "Ort. 1A Getiri %",
            "ort_getiri_3a": "Ort. 3A Getiri %",
            "ort_skor": "Ort. Getiri Skoru %",
            "en_iyi_kod": "En İyi Fon",
            "en_iyi_ad": "En İyi Fon Adı",
            "en_iyi_skor": "En İyi Fon Skoru %",
        }
    )
    st.dataframe(
        tema_tablo,
        width="stretch",
        height=400,
        column_config={
            "Tema": st.column_config.TextColumn(help="Fon adından tahmin edilen sektör/tema etiketi."),
            "Fon Sayısı": st.column_config.NumberColumn(help="Bu temada, güvenilirlik filtresini geçen fon sayısı."),
            "Ort. 1A Getiri %": st.column_config.NumberColumn(help="Bu temadaki fonların ortalama 1 aylık getirisi.", format="%.2f%%"),
            "Ort. 3A Getiri %": st.column_config.NumberColumn(help="Bu temadaki fonların ortalama 3 aylık getirisi.", format="%.2f%%"),
            "Ort. Getiri Skoru %": st.column_config.NumberColumn(help="1a/3a/6a getirilerinin ortalaması; sıralama bu skora göre yapılır."),
            "En İyi Fon": st.column_config.TextColumn(help="Bu temada en yüksek getiri skoruna sahip fon."),
            "En İyi Fon Skoru %": st.column_config.NumberColumn(help="En iyi fonun getiri skoru."),
        },
    )
    st.caption(
        "Yalnızca güvenilirlik filtresini geçen fonlar dahildir (büyüklük ≥ 10 mn TL, yatırımcı ≥ 20, "
        "anomali getiriler hariç). 'Genel / Karma' etiketi, fonun adından tema tahmin edilemediği anlamına gelir."
    )

st.divider()

# ---------------- Hisse sektorleri ----------------
st.subheader("⚡ Hisse Sektörleri Sıralaması")
sektor_perf = umbrella.stock_sector_performance(stocks_df)
if sektor_perf.empty:
    st.info("Hisse verisi çekilemedi, lütfen verileri yenileyin.")
else:
    chart_df = sektor_perf.sort_values("ort_skor", ascending=True)
    fig = px.bar(
        chart_df,
        x="ort_skor",
        y="sektor",
        orientation="h",
        title="Hisse Sektörleri — Ortalama Teknik Skor",
        labels={"ort_skor": "Ortalama teknik skor", "sektor": ""},
        color_discrete_sequence=[CHART_COLORS[1]],
    )
    fig.update_layout(height=max(360, 32 * len(chart_df)))
    st.plotly_chart(fig, width="stretch")

    sektor_tablo = sektor_perf.rename(
        columns={
            "sektor": "Sektör",
            "hisse_sayisi": "Hisse Sayısı",
            "ort_skor": "Ort. Teknik Skor",
            "ort_momentum_5g": "Ort. 5G Momentum %",
            "en_iyi_kod": "En İyi Hisse",
            "en_iyi_skor": "En İyi Hisse Skoru",
        }
    )
    st.dataframe(
        sektor_tablo,
        width="stretch",
        height=400,
        column_config={
            "Sektör": st.column_config.TextColumn(help="Elle hazırlanmış sabit sektör haritasından gelen etiket."),
            "Hisse Sayısı": st.column_config.NumberColumn(help="Bu sektörde izleme listesinde bulunan hisse sayısı."),
            "Ort. Teknik Skor": st.column_config.NumberColumn(help="Sektördeki hisselerin ortalama teknik skoru (trend+RSI+hacim+momentum)."),
            "Ort. 5G Momentum %": st.column_config.NumberColumn(help="Sektördeki hisselerin ortalama 5 günlük momentumu.", format="%.2f%%"),
            "En İyi Hisse": st.column_config.TextColumn(help="Bu sektörde en yüksek teknik skora sahip hisse."),
            "En İyi Hisse Skoru": st.column_config.NumberColumn(help="En iyi hissenin teknik skoru."),
        },
    )
    st.caption(
        "Sektör etiketleri, izleme listesindeki hisseler için elle hazırlanmış sabit bir haritadan gelir "
        "(borsa/resmi kaynak verisi değildir). Skor formülü Günlük İşlem Analizi sayfasıyla aynıdır."
    )
