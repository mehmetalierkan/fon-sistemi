"""Ortak gorsel tema: canli renkli sidebar/kartlar/butonlar ve gradient basliklar."""
import streamlit as st

_CSS = """
<style>
/* --- Genel sayfa zemini: artik duz beyaz degil, hafif mavimsi gradient --- */
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.main {
    background: linear-gradient(160deg, #EFF6FF 0%, #ECFEFF 45%, #F0FDFA 100%) !important;
}
[data-testid="stHeader"] {
    background: transparent !important;
}

/* --- Sidebar: canli mavi gradient, ikonlu nav --- */
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
    border-radius: 12px;
}
[data-testid="stSidebarNav"] li {
    margin: 2px 10px;
}
[data-testid="stSidebarNav"] a {
    padding: 10px 14px !important;
    transition: background-color 0.15s ease, transform 0.1s ease;
}
[data-testid="stSidebarNav"] a:hover {
    background-color: rgba(255,255,255,0.16);
    transform: translateX(2px);
}
[data-testid="stSidebarNav"] a[aria-current="page"] {
    background-color: rgba(255,255,255,0.26);
    font-weight: 700;
    box-shadow: inset 3px 0 0 #FDE68A;
}
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.25);
}

/* --- Metric kartlari --- */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #DBEAFE 0%, #ECFEFF 100%);
    border: 1.5px solid #60A5FA;
    border-top: 5px solid #2563EB;
    border-radius: 14px;
    padding: 16px 18px;
    box-shadow: 0 6px 18px rgba(37, 99, 235, 0.20);
}
[data-testid="stMetricLabel"] {
    font-weight: 600;
    color: #1D4ED8 !important;
}
[data-testid="stMetricValue"] {
    color: #172554 !important;
}

/* --- Basliklar (subheader/header) - renkli sol serit + hafif zemin --- */
[data-testid="stMain"] h2,
[data-testid="stMain"] h3 {
    border-left: 5px solid #2563EB;
    padding: 4px 0 4px 14px;
    background: linear-gradient(90deg, rgba(37, 99, 235, 0.10), rgba(37, 99, 235, 0) 80%);
    border-radius: 6px;
}

/* --- Girdi kutulari (selectbox/number/text/date) - renkli kenarlik --- */
[data-testid="stSelectbox"] [role="group"],
[data-testid="stNumberInputContainer"],
[data-testid="stTextInput"] [role="group"],
[data-testid="stDateInput"] [role="group"],
[data-testid="stTextArea"] [role="group"] {
    border: 2px solid #60A5FA !important;
    border-radius: 10px !important;
    background-color: #F8FBFF !important;
}
[data-testid="stSelectbox"] [role="group"]:focus-within,
[data-testid="stNumberInputContainer"]:focus-within,
[data-testid="stTextInput"] [role="group"]:focus-within,
[data-testid="stDateInput"] [role="group"]:focus-within {
    border-color: #2563EB !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.18) !important;
}

/* --- Ayirici cizgiler --- */
[data-testid="stMain"] hr {
    height: 3px !important;
    border: none !important;
    background: linear-gradient(90deg, #2563EB, #06B6D4, #0D9488) !important;
    opacity: 0.55;
    border-radius: 3px;
}

/* --- Expander kutulari --- */
[data-testid="stExpander"] {
    border: 1px solid #BFDBFE !important;
    border-radius: 14px !important;
    background: linear-gradient(135deg, #F8FBFF, #F0FDFA) !important;
    box-shadow: 0 3px 10px rgba(37, 99, 235, 0.08);
}

/* --- Dataframe cercevesi --- */
[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid #BFDBFE;
}

/* --- Uyari/bilgi kutulari --- */
[data-testid="stAlert"] {
    border-radius: 12px;
}

/* --- Butonlar --- */
.stButton>button, .stFormSubmitButton>button, .stDownloadButton>button {
    background: linear-gradient(90deg, #2563EB, #06B6D4);
    color: white;
    border: none;
    border-radius: 12px;
    font-weight: 700;
    padding: 0.55rem 1.1rem;
    transition: filter 0.15s ease, transform 0.1s ease;
}
.stButton>button:hover, .stFormSubmitButton>button:hover, .stDownloadButton>button:hover {
    filter: brightness(1.08);
    transform: translateY(-1px);
    color: white;
}

/* --- Basliklar --- */
.gradient-title {
    background: linear-gradient(90deg, #2563EB, #06B6D4 55%, #0D9488);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800;
    padding-bottom: 0.2rem;
}
.gradient-subtitle {
    color: #1D4ED8;
    font-weight: 600;
}

/* --- Sekmeler (tabs) --- */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
}
.stTabs [data-baseweb="tab"] {
    background-color: #EFF6FF;
    border-radius: 10px 10px 0 0;
    padding: 8px 16px;
    font-weight: 600;
}
.stTabs [aria-selected="true"] {
    background-color: #DBEAFE;
    color: #1D4ED8 !important;
}

/* --- Expander basliklari --- */
[data-testid="stExpander"] summary {
    font-weight: 600;
    border-radius: 10px;
}

/* --- Sayfa-ici linkler (st.page_link): uzun aciklayici etiketler tek satira sikismasin --- */
[data-testid="stPageLink-NavLink"] p,
[data-testid="stPageLink-NavLink"] span {
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: unset !important;
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
