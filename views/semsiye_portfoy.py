"""Sektor/tema hedefli semsiye portfoy olusturma sayfasi (fon ve hisse portfoyleri AYRI ayri)."""
import datetime as dt

import pandas as pd
import plotly.express as px
import streamlit as st

from analysis import daily_screener, umbrella
from data import tefas_client
from portfolio import db
from ui import CHART_COLORS, cap_categories, gradient_title

gradient_title("Şemsiye Portföy Oluşturucu", "🌂")
st.caption(
    "Sektör/tema hedeflerinizi yüzdelerle girin (ör. %10 Teknoloji, %50 Yenilenebilir Enerji); sistem her "
    "başlık için TEFAS fonları ve BIST izleme listesindeki hisseler arasından mevcut skorlama kriterleriyle "
    "en iyi adayları seçer. **Fon ve hisse önerileri ayrı ayrı** (kendi bütçenizle) oluşturulur, her biri "
    "tek başına **5 ile 10 arasında** enstrüman içerir. "
    "**Önemli sınır:** fon-sektör eşleşmesi fonun adından tahmindir (TEFAS kesin sektör verisi vermez), "
    "hisse-sektör eşleşmesi ise elle hazırlanmış sabit bir haritadan gelir. Kriterlerin tam açıklaması için "
    "sol menüden **🧭 Nasıl Değerlendiriyoruz?** sayfasına bakabilirsiniz."
)
col_a, col_b, col_c = st.columns([1, 1, 1], vertical_alignment="bottom")
with col_a:
    fund_budget = st.number_input(
        "Fon Bütçesi (TL)", min_value=0.0, value=float(db.get_balance("FUND")), step=1_000.0,
        help="Varsayılan: Portföyüm sayfasındaki güncel Haftalık Fon Kasası nakit bakiyeniz.",
    )
with col_b:
    stock_budget = st.number_input(
        "Hisse Bütçesi (TL)", min_value=0.0, value=float(db.get_balance("DAILY")), step=500.0,
        help="Varsayılan: Portföyüm sayfasındaki güncel Günlük İşlem Kasası nakit bakiyeniz.",
    )
with col_c:
    if st.button("🔄 Verileri Yenile"):
        st.cache_data.clear()
        st.rerun()

st.subheader("Hedef Sektör / Tema Dağılımı")
st.caption(
    "Tablodan satır ekleyip çıkarabilirsiniz. Bu dağılım hem fon hem hisse şemsiyesi için ortak kullanılır. "
    "Yüzdelerin toplamı 100 değilse otomatik normalize edilir ve bu size bildirilir."
)

_DEFAULT_TARGETS = pd.DataFrame(
    [
        {"Sektör / Tema": "Teknoloji", "Hedef %": 10.0},
        {"Sektör / Tema": "Yenilenebilir Enerji", "Hedef %": 50.0},
        {"Sektör / Tema": "Bankacılık / Finans", "Hedef %": 25.0},
        {"Sektör / Tema": "Kıymetli Maden", "Hedef %": 15.0},
    ]
)

with st.expander("🧙 Sektör Hedeflerini Belirlemekte Zorlanıyor musunuz? Soru-Cevapla Öneri Alın", expanded=False):
    st.caption(
        "Birkaç soruyu cevaplayın; sistem kural tabanlı bir mantıkla (risk toleransı + vade + öncelik → "
        "sektör risk profili eşleştirmesi) size başlangıç için bir hedef dağılım önersin. Öneri, aşağıdaki "
        "tabloyu otomatik doldurur — dilediğiniz gibi düzenlemeye devam edebilirsiniz."
    )
    with st.form("sektor_sihirbazi"):
        secilen_sektorler = st.multiselect(
            "İlgilendiğiniz sektör/temalar (birden fazla seçebilirsiniz)",
            umbrella.SECTOR_OPTIONS,
            default=["Teknoloji", "Bankacılık / Finans", "Kıymetli Maden"],
        )
        wc1, wc2, wc3 = st.columns(3)
        vade = wc1.radio("Yatırım vadeniz", umbrella.WIZARD_VADE_OPTIONS, index=1)
        risk_toleransi = wc2.radio("Risk toleransınız", umbrella.WIZARD_RISK_OPTIONS, index=1)
        oncelik = wc3.radio("Önceliğiniz", umbrella.WIZARD_ONCELIK_OPTIONS, index=1)
        wizard_submitted = st.form_submit_button("✨ Hedef Sektörleri Öner")

    if wizard_submitted:
        if not secilen_sektorler:
            st.warning("En az bir sektör/tema seçin.")
        else:
            wizard_targets, wizard_gerekce = umbrella.wizard_recommend_targets(
                secilen_sektorler, risk_toleransi, vade, oncelik
            )
            st.session_state["wizard_targets_df"] = pd.DataFrame(
                [{"Sektör / Tema": s, "Hedef %": p} for s, p in wizard_targets]
            )
            st.session_state["wizard_version"] = st.session_state.get("wizard_version", 0) + 1
            st.info(wizard_gerekce)

_source_targets = st.session_state.get("wizard_targets_df", _DEFAULT_TARGETS)
_editor_key = f"hedef_editor_{st.session_state.get('wizard_version', 0)}"
edited = st.data_editor(
    _source_targets,
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
    key=_editor_key,
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


@st.cache_data(ttl=3600, show_spinner="Fon şemsiyesi oluşturuluyor...")
def _build_funds(targets_t: tuple, budget_tl: float, as_of_str: str):
    funds = _load_funds(as_of_str)
    return umbrella.build_fund_umbrella_portfolio(list(targets_t), budget_tl, funds)


@st.cache_data(ttl=900, show_spinner="Hisse şemsiyesi oluşturuluyor...")
def _build_stocks(targets_t: tuple, budget_tl: float):
    stocks = _load_stocks()
    return umbrella.build_stock_umbrella_portfolio(list(targets_t), budget_tl, stocks)


def _render_portfolio(title: str, icon: str, df: pd.DataFrame, notes: list, tur_label: str, is_fund: bool) -> None:
    st.divider()
    st.subheader(f"{icon} {title}")
    for level, text in notes:
        (st.warning if level == "warning" else st.info)(text)
    if df.empty:
        st.info(f"Girilen hedeflere uygun {tur_label} önerisi oluşturulamadı. Farklı sektörler deneyin veya verileri yenileyin.")
        return

    m1, m2, m3 = st.columns(3)
    m1.metric(f"Toplam {tur_label.capitalize()}", f"{len(df)} adet")
    m2.metric("Sektör Sayısı", f"{df['sektor'].nunique()}")
    m3.metric("Dağıtılan Bütçe", f"{df['tutar_tl'].sum():,.0f} TL")

    for _, row in df.iterrows():
        baslik = f"**{row['kod']}** · {row['sektor']} — {row['tutar_tl']:,.0f} TL (%{row['hedef_pct']:.1f})"
        with st.expander(baslik, expanded=False):
            if is_fund:
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

    sektor_dagilim = df.groupby("sektor")["tutar_tl"].sum().sort_values(ascending=False)
    capped = cap_categories([(k, float(v)) for k, v in sektor_dagilim.items()])
    fig = px.pie(
        names=[x[0] for x in capped],
        values=[x[1] for x in capped],
        title=f"{title} — Sektör Bazında Dağılım (TL)",
        color_discrete_sequence=CHART_COLORS,
    )
    st.plotly_chart(fig, width="stretch", key=f"pie_{tur_label}")

    ozet = df[
        ["kod", "ad", "sektor", "hedef_pct", "tutar_tl", "getiri_1a", "getiri_3a", "yillik_volatilite_pct", "skor"]
    ].rename(
        columns={
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
    st.dataframe(
        ozet,
        width="stretch",
        column_config={
            "Kod": st.column_config.TextColumn(help="Fon veya hisse kodu."),
            "Sektör / Tema": st.column_config.TextColumn(help="Hedef tabloda girdiğiniz sektör/tema başlığı."),
            "Pay %": st.column_config.NumberColumn(help="Bu enstrümanın toplam bütçe içindeki payı.", format="%.1f%%"),
            "Tutar (TL)": st.column_config.NumberColumn(help="Bu enstrümana ayrılan TL tutarı."),
            "1A Getiri % (fon)": st.column_config.NumberColumn(help="Sadece fonlar için: son 1 aylık getiri.", format="%.2f%%"),
            "3A Getiri % / 5G Momentum %": st.column_config.NumberColumn(help="Fonlarda 3 aylık getiri, hisselerde 5 günlük momentum.", format="%.2f%%"),
            "Yıllık Vol. % (fon)": st.column_config.NumberColumn(help="Sadece fonlar için: yıllıklandırılmış volatilite (risk göstergesi)."),
            "Skor": st.column_config.NumberColumn(help="Fonlarda getiri/volatilite oranı, hisselerde teknik skor; seçim bu skora göre yapılır."),
        },
    )


as_of = dt.date.today()

try:
    fund_df, fund_notes = _build_funds(tuple(targets), float(fund_budget), as_of.isoformat())
except Exception as exc:
    fund_df, fund_notes = pd.DataFrame(), [("warning", f"Fon verisi çekilirken hata oluştu: {exc}")]

try:
    stock_df, stock_notes = _build_stocks(tuple(targets), float(stock_budget))
except Exception as exc:
    stock_df, stock_notes = pd.DataFrame(), [("warning", f"Hisse verisi çekilirken hata oluştu: {exc}")]

_render_portfolio("Fon Şemsiyesi", "📈", fund_df, fund_notes, "fon", is_fund=True)
_render_portfolio("Hisse Şemsiyesi", "⚡", stock_df, stock_notes, "hisse", is_fund=False)

st.divider()
st.caption(
    "Bu tablolar birer anlık görüntüdür (snapshot); fon evreni 1 saat, hisse taraması 15 dakika önbelleklenir. "
    "**🔄 Verileri Yenile** ile güncel veri çekebilirsiniz."
)
