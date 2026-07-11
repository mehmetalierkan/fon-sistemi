"""Ortak gorsel tema: sakin 'finans terminali' duzeni.

Tasarim sistemi (degistirirken tutarli kal):
- Renk: murekkep #0F172A, soluk #64748B, cizgi #E2E8F0, ana MAVI #2563EB / koyu #1D4ED8,
  zemin #F6F8FC, yuzey #FFFFFF. Tek sicak vurgu: sidebar aktif cizgisi #FDE68A.
- Tipografi: IBM Plex Sans (metin/basliklar) + IBM Plex Mono (metric degerleri, tabular rakam).
- Tek "yuksek sesli" alan canli mavi sidebar'dir; icerik alani beyaz kart + ince cizgi ile sakindir.
- Turkce metinlerde CSS text-transform: uppercase KULLANMA (i -> I donusumu bozulur).
"""
import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');

/* --- Tipografi tabani --- */
html, body, p, li, label, input, textarea, button,
h1, h2, h3, h4, h5, h6, .stApp {
    font-family: "IBM Plex Sans", "Segoe UI", system-ui, sans-serif;
}
[data-testid="stMain"] h1,
[data-testid="stMain"] h2,
[data-testid="stMain"] h3 {
    color: #0F172A;
    letter-spacing: -0.01em;
}

/* --- Genel sayfa zemini: sakin, duz, soguk beyaz --- */
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.main {
    background: #F6F8FC !important;
}
[data-testid="stHeader"] {
    background: transparent !important;
}

/* --- Sidebar: canli mavi gradient (uygulamanin tek 'yuksek sesli' alani) --- */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #2563EB 0%, #1D4ED8 55%, #172554 100%);
}
[data-testid="stSidebar"] * {
    color: #FFFFFF !important;
}
[data-testid="stSidebarNav"] {
    padding-top: 0.75rem;
}
[data-testid="stSidebarNav"] a,
[data-testid="stSidebarNav"] span[data-testid="stIconMaterial"] {
    border-radius: 10px;
}
[data-testid="stSidebarNav"] li {
    margin: 2px 10px;
}
[data-testid="stSidebarNav"] a {
    padding: 9px 14px !important;
    transition: background-color 0.15s ease, transform 0.1s ease;
}
[data-testid="stSidebarNav"] a:hover {
    background-color: rgba(255,255,255,0.14);
    transform: translateX(2px);
}
[data-testid="stSidebarNav"] a[aria-current="page"] {
    background-color: rgba(255,255,255,0.22);
    font-weight: 700;
    box-shadow: inset 3px 0 0 #FDE68A;
}
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.25);
}

/* --- Metric kartlari: beyaz yuzey, ince cizgi, ustte mavi serit; degerler mono/tabular --- */
[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-top: 3px solid #2563EB;
    border-radius: 10px;
    padding: 14px 16px;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
}
[data-testid="stMetricLabel"] {
    color: #64748B !important;
}
[data-testid="stMetricLabel"] p {
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.02em;
}
[data-testid="stMetricValue"] {
    font-family: "IBM Plex Mono", "Consolas", monospace;
    font-variant-numeric: tabular-nums;
    font-weight: 600;
    color: #0F172A !important;
}
[data-testid="stMetricDelta"] {
    font-family: "IBM Plex Mono", "Consolas", monospace;
    font-variant-numeric: tabular-nums;
}

/* --- Basliklar: h2 ince alt cizgi (bolum), h3 ince mavi sol tik (alt bolum) --- */
[data-testid="stMain"] h2 {
    padding-bottom: 0.35rem;
    border-bottom: 1px solid #E2E8F0;
}
[data-testid="stMain"] h3 {
    border-left: 3px solid #2563EB;
    padding-left: 10px;
}

/* --- Girdi kutulari: ince notr kenarlik, odakta mavi halka --- */
[data-testid="stSelectbox"] [role="group"],
[data-testid="stNumberInputContainer"],
[data-testid="stTextInput"] [role="group"],
[data-testid="stDateInput"] [role="group"],
[data-testid="stTextArea"] [role="group"] {
    border: 1px solid #CBD5E1 !important;
    border-radius: 8px !important;
    background-color: #FFFFFF !important;
}
[data-testid="stSelectbox"] [role="group"]:focus-within,
[data-testid="stNumberInputContainer"]:focus-within,
[data-testid="stTextInput"] [role="group"]:focus-within,
[data-testid="stDateInput"] [role="group"]:focus-within {
    border-color: #2563EB !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15) !important;
}

/* --- Ayirici cizgiler: sessiz tek cizgi --- */
[data-testid="stMain"] hr {
    height: 1px !important;
    border: none !important;
    background: #E2E8F0 !important;
    opacity: 1;
}

/* --- Expander kutulari: beyaz kart --- */
[data-testid="stExpander"] {
    border: 1px solid #E2E8F0 !important;
    border-radius: 10px !important;
    background: #FFFFFF !important;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}
[data-testid="stExpander"] summary {
    font-weight: 600;
    border-radius: 10px;
}
[data-testid="stExpander"] summary:hover {
    color: #1D4ED8;
}

/* --- Dataframe cercevesi --- */
[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid #E2E8F0;
    background: #FFFFFF;
}

/* --- Uyari/bilgi kutulari --- */
[data-testid="stAlert"] {
    border-radius: 10px;
}

/* --- Butonlar: duz mavi, hover'da koyu mavi; gorunur klavye odagi --- */
.stButton>button, .stFormSubmitButton>button, .stDownloadButton>button {
    background: #2563EB;
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 0.5rem 1.05rem;
    box-shadow: 0 1px 2px rgba(37, 99, 235, 0.25);
    transition: background-color 0.15s ease;
}
.stButton>button:hover, .stFormSubmitButton>button:hover, .stDownloadButton>button:hover {
    background: #1D4ED8;
    color: white;
}
.stButton>button:focus-visible, .stFormSubmitButton>button:focus-visible, .stDownloadButton>button:focus-visible {
    outline: 3px solid rgba(37, 99, 235, 0.35);
    outline-offset: 2px;
}

/* --- Sayfa basligi: murekkep renkli, siki takip; altinda kisa mavi imza cizgisi --- */
.gradient-title {
    color: #0F172A;
    font-weight: 700;
    letter-spacing: -0.02em;
    padding-bottom: 0;
    margin-bottom: 0.35rem;
}
.gradient-title::after {
    content: "";
    display: block;
    width: 52px;
    height: 4px;
    margin-top: 10px;
    border-radius: 2px;
    background: linear-gradient(90deg, #2563EB, #60A5FA);
}
.gradient-subtitle {
    color: #1D4ED8;
    font-weight: 600;
}
.lead {
    font-size: 1.05rem;
    color: #475569;
    max-width: 68ch;
}

/* --- Sekmeler (tabs): kutu yerine sessiz alt-cizgi stili --- */
.stTabs [data-baseweb="tab-list"] {
    gap: 2px;
    border-bottom: 1px solid #E2E8F0;
}
.stTabs [data-baseweb="tab"] {
    background-color: transparent;
    border-radius: 8px 8px 0 0;
    padding: 8px 14px;
    font-weight: 600;
    color: #64748B;
}
.stTabs [aria-selected="true"] {
    background-color: transparent;
    color: #1D4ED8 !important;
}
.stTabs [data-baseweb="tab-highlight"] {
    background-color: #2563EB;
}

/* --- Sayfa-ici linkler (st.page_link): uzun aciklayici etiketler tek satira sikismasin --- */
[data-testid="stPageLink-NavLink"] p,
[data-testid="stPageLink-NavLink"] span {
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: unset !important;
}

/* --- Hareket azaltma tercihi --- */
@media (prefers-reduced-motion: reduce) {
    * {
        transition: none !important;
        animation: none !important;
    }
    [data-testid="stSidebarNav"] a:hover {
        transform: none;
    }
}

/* --- Mobil / dar ekran duzeltmeleri --- */
@media (max-width: 640px) {
    .gradient-title {
        font-size: 1.7rem !important;
        line-height: 1.25 !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.4rem !important;
    }
    [data-testid="stMain"] .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    [data-testid="stMetric"] {
        padding: 10px 12px;
    }
}

</style>
"""


def apply_theme() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def gradient_title(text: str, emoji: str = "") -> None:
    prefix = f"{emoji} " if emoji else ""
    st.markdown(f'<h1 class="gradient-title">{prefix}{text}</h1>', unsafe_allow_html=True)


def recommendation_faq(neden: str, sure: str) -> None:
    """Al/Sat veya siralama onerisi iceren her sayfada tekrar eden SSS blogu.

    neden: bu sayfanin oneri/sinyal uretme AMACINI aciklayan metin.
    sure: onerinin ne kadar sureyle gecerli/anlamli oldugunu aciklayan metin.
    """
    with st.expander("❓ Neden bu öneriler var, ne kadar süre geçerli?", expanded=False):
        st.markdown(f"**Neden bu öneriler sunuluyor?** {neden}")
        st.markdown(f"**Ne kadar süre için geçerli?** {sure}")


# Dogrulanmis kategorik palet (CVD-guvenli sira, bkz. dataviz skill referans paleti).
# Sira sabit tutulmali - hue'lar rastgele atanmamali.
CHART_COLORS: list[str] = [
    "#2a78d6",  # mavi
    "#1baf7a",  # turkuaz
    "#eda100",  # sari/altin
    "#008300",  # yesil
    "#4a3aa7",  # mor
    "#e34948",  # kirmizi
    "#e87ba4",  # pembe
    "#eb6834",  # turuncu
]


def cap_categories(items: list[tuple[str, float]], max_slices: int = 7) -> list[tuple[str, float]]:
    """9+ dilimli pasta grafiklerde artan kategorileri 'Diger' altinda toplar (hue tukenmesin diye)."""
    if len(items) <= max_slices:
        return items
    kept = list(items[:max_slices])
    rest_sum = sum(v for _, v in items[max_slices:])
    if rest_sum > 0:
        kept.append(("Diğer", rest_sum))
    return kept
