"""Fon & BIST Hisse Analiz/Öneri Sistemi - giris noktasi (ozel ikonlu/renkli navigasyon)."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

import streamlit as st

from ui import apply_theme

st.set_page_config(page_title="Fon & Hisse Analiz Sistemi", page_icon="📊", layout="wide")
apply_theme()

home = st.Page("views/home.py", title="Ana Sayfa", icon="🏠", default=True)
weekly = st.Page("views/weekly_fund.py", title="Haftalık Fon Analizi", icon="📈")
daily = st.Page("views/daily_stock.py", title="Günlük İşlem Analizi", icon="⚡")
portfolio_page = st.Page("views/portfolio.py", title="Portföyüm", icon="💼")
umbrella_page = st.Page("views/semsiye_portfoy.py", title="Şemsiye Portföy Oluşturucu", icon="🌂")
sector_page = st.Page("views/sektorel_performans.py", title="Sektörel Performans", icon="🏆")
methodology = st.Page("views/methodology.py", title="Nasıl Değerlendiriyoruz?", icon="🧭")

pg = st.navigation([home, weekly, daily, portfolio_page, umbrella_page, sector_page, methodology])
pg.run()
