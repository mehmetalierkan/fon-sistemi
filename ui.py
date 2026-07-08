"""Ortak gorsel tema: canli renkli sidebar/kartlar/butonlar ve gradient basliklar."""
import streamlit as st

_CSS = """
<style>
/* --- Genel sayfa zemini: artik duz beyaz degil, hafif renkli gradient --- */
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.main {
    background: linear-gradient(160deg, #FAF5FF 0%, #FDF2F8 45%, #FFF9F2 100%) !important;
}
[data-testid="stHeader"] {
    background: transparent !important;
}

/* --- Sidebar: canli mor-pembe gradient, ikonlu nav --- */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #7C3AED 0%, #5B21B6 55%, #3B0764 100%);
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
    background: linear-gradient(135deg, #F3E8FF 0%, #FDF2F8 100%);
    border: 1.5px solid #A78BFA;
    border-top: 5px solid #7C3AED;
    border-radius: 14px;
    padding: 16px 18px;
    box-shadow: 0 6px 18px rgba(124, 58, 237, 0.20);
}
[data-testid="stMetricLabel"] {
    font-weight: 600;
    color: #6D28D9 !important;
}
[data-testid="stMetricValue"] {
    color: #3B0764 !important;
}

/* --- Basliklar (subheader/header) - renkli sol serit + hafif zemin --- */
[data-testid="stMain"] h2,
[data-testid="stMain"] h3 {
    border-left: 5px solid #7C3AED;
    padding: 4px 0 4px 14px;
    background: linear-gradient(90deg, rgba(124, 58, 237, 0.10), rgba(124, 58, 237, 0) 80%);
    border-radius: 6px;
}

/* --- Girdi kutulari (selectbox/number/text/date) - renkli kenarlik --- */
[data-testid="stSelectbox"] [role="group"],
[data-testid="stNumberInputContainer"],
[data-testid="stTextInput"] [role="group"],
[data-testid="stDateInput"] [role="group"],
[data-testid="stTextArea"] [role="group"] {
    border: 2px solid #A78BFA !important;
    border-radius: 10px !important;
    background-color: #FDFBFF !important;
}
[data-testid="stSelectbox"] [role="group"]:focus-within,
[data-testid="stNumberInputContainer"]:focus-within,
[data-testid="stTextInput"] [role="group"]:focus-within,
[data-testid="stDateInput"] [role="group"]:focus-within {
    border-color: #7C3AED !important;
    box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.18) !important;
}

/* --- Ayirici cizgiler --- */
[data-testid="stMain"] hr {
    height: 3px !important;
    border: none !important;
    background: linear-gradient(90deg, #7C3AED, #EC4899, #F97316) !important;
    opacity: 0.55;
    border-radius: 3px;
}

/* --- Expander kutulari --- */
[data-testid="stExpander"] {
    border: 1px solid #E9D5FF !important;
    border-radius: 14px !important;
    background: linear-gradient(135deg, #FDFBFF, #FFF7FB) !important;
    box-shadow: 0 3px 10px rgba(124, 58, 237, 0.08);
}

/* --- Dataframe cercevesi --- */
[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid #E9D5FF;
}

/* --- Uyari/bilgi kutulari --- */
[data-testid="stAlert"] {
    border-radius: 12px;
}

/* --- Butonlar --- */
.stButton>button, .stFormSubmitButton>button, .stDownloadButton>button {
    background: linear-gradient(90deg, #7C3AED, #EC4899);
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
    background: linear-gradient(90deg, #7C3AED, #EC4899 55%, #F97316);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800;
    padding-bottom: 0.2rem;
}
.gradient-subtitle {
    color: #6D28D9;
    font-weight: 600;
}

/* --- Sekmeler (tabs) --- */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
}
.stTabs [data-baseweb="tab"] {
    background-color: #F5F3FF;
    border-radius: 10px 10px 0 0;
    padding: 8px 16px;
    font-weight: 600;
}
.stTabs [aria-selected="true"] {
    background-color: #EDE9FE;
    color: #6D28D9 !important;
}

/* --- Expander basliklari --- */
[data-testid="stExpander"] summary {
    font-weight: 600;
    border-radius: 10px;
}

</style>
"""


def apply_theme() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def gradient_title(text: str, emoji: str = "") -> None:
    prefix = f"{emoji} " if emoji else ""
    st.markdown(f'<h1 class="gradient-title">{prefix}{text}</h1>', unsafe_allow_html=True)


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
