"""Ana sayfa - genel bakis."""
import streamlit as st

from portfolio import db
from ui import gradient_title

db.init_db()

st.warning(
    "⚠️ Bu sistem yalnızca bilgilendirme ve analiz amaçlıdır, yatırım tavsiyesi değildir. "
    "Tüm alım-satım kararları ve emirleri size aittir. Sistem Midas'a veya başka bir aracı kuruma "
    "otomatik bağlanmaz; gerçekleştirdiğiniz işlemleri Portföyüm sayfasından elle girmeniz gerekir."
)

gradient_title("Fon & BIST Hisse Analiz Sistemi", "📊")
st.markdown(
    """
Bu panel iki ayrı yatırım döngünüz için analiz ve öneri üretir:

- **📈 Haftalık Fon Analizi** — her Pazartesi, 20.000 TL'lik fon bütçeniz için TEFAS fon karşılaştırması,
  varlık dağılımı ve gerekçeli öneriler.
- **⚡ Günlük İşlem Analizi** — her sabah, 10.000 TL'lik Midas işlem bütçeniz için BIST hisse teknik taraması
  ve gerekçeli öneriler.
- **💼 Portföyüm** — her iki kasanın bakiyesi, mevcut pozisyonlar ve işlem geçmişi.
- **🧭 Nasıl Değerlendiriyoruz?** — sistemin fon/hisse seçerken hangi kriterlere baktığının detaylı anlatımı.

Sol menüden bir sayfa seçin. Her sayfada **"Verileri Yenile"** butonuna basarak TEFAS/BIST'ten güncel veri
çekebilirsiniz.
"""
)

col1, col2 = st.columns(2)
with col1:
    st.metric("Haftalık Fon Kasası - Nakit Bakiye", f"{db.get_balance('FUND'):,.2f} TL")
with col2:
    st.metric("Günlük İşlem Kasası - Nakit Bakiye", f"{db.get_balance('DAILY'):,.2f} TL")
