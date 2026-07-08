"""Portfoy: iki kasa (haftalik fon / gunluk hisse) - bakiye, pozisyonlar, islem gecmisi ve yeni islem girisi."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import datetime as dt

import pandas as pd
import streamlit as st

from data import stock_client, tefas_client
from portfolio import db

st.set_page_config(page_title="Portföyüm", page_icon="💼", layout="wide")

db.init_db()

st.title("💼 Portföyüm")
st.caption(
    "Buradaki bakiyeler ve pozisyonlar, aşağıdaki formdan elle girdiğiniz işlemlere göre hesaplanır. "
    "Sistem hiçbir aracı kuruma (Midas dahil) otomatik bağlanmaz; gerçekleştirdiğiniz her alım/satımı "
    "burada kendiniz kaydetmeniz gerekir."
)


def _fund_price_lookup(code: str) -> float | None:
    try:
        hist = tefas_client.get_fund_price_history(code, periyod_ay=1)
        if not hist.empty:
            return float(hist.iloc[-1]["fiyat"])
    except Exception:
        pass
    return None


def _stock_price_lookup(code: str) -> float | None:
    try:
        quote = stock_client.get_stock_quote(code)
        return quote.get("fiyat")
    except Exception:
        return None


def _render_bucket(bucket: str, label: str, price_lookup, code_help: str) -> None:
    st.header(label)
    summary = db.get_portfolio_summary(bucket, price_lookup)

    m1, m2, m3 = st.columns(3)
    m1.metric("Nakit Bakiye", f"{summary['bakiye']:,.2f} TL")
    m2.metric("Pozisyon Değeri", f"{summary['pozisyon_degeri']:,.2f} TL")
    m3.metric("Toplam Değer", f"{summary['toplam_deger']:,.2f} TL")

    if summary["pozisyonlar"]:
        rows = []
        for code, pos in summary["pozisyonlar"].items():
            rows.append({
                "Kod": code,
                "Ad": pos["instrument_name"],
                "Adet": pos["quantity"],
                "Ort. Maliyet": pos["avg_cost"],
                "Güncel Fiyat": pos["guncel_fiyat"],
                "Piyasa Değeri": pos["piyasa_degeri"],
                "Gerçekleşmemiş K/Z": pos["gerceklesmemis_kz"],
                "Gerçekleşmiş K/Z": pos["realized_pnl"],
            })
        st.dataframe(pd.DataFrame(rows), width="stretch")
    else:
        st.info("Henüz açık pozisyon yok.")

    with st.expander("➕ Yeni İşlem Ekle"):
        with st.form(f"form_{bucket}", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            code = c1.text_input("Kod", help=code_help, key=f"code_{bucket}")
            name = c2.text_input("Ad (opsiyonel)", key=f"name_{bucket}")
            side = c3.selectbox("İşlem", ["BUY", "SELL"], format_func=lambda x: "Alış" if x == "BUY" else "Satış", key=f"side_{bucket}")
            c4, c5, c6 = st.columns(3)
            qty = c4.number_input("Adet", min_value=0.0, step=1.0, key=f"qty_{bucket}")
            price = c5.number_input("Fiyat (birim, TL)", min_value=0.0, step=0.01, key=f"price_{bucket}")
            trade_date = c6.date_input("Tarih", value=dt.date.today(), key=f"date_{bucket}")
            submitted = st.form_submit_button("Kaydet")
            if submitted:
                try:
                    db.add_transaction(bucket, code, name, side, qty, price, trade_date)
                    st.success(f"{code.upper()} için {qty} adet {side} işlemi kaydedildi.")
                    st.cache_data.clear()
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

    transactions = db.get_transactions(bucket)
    if transactions:
        with st.expander("İşlem Geçmişi"):
            tx_rows = [dict(row) for row in transactions]
            st.dataframe(pd.DataFrame(tx_rows), width="stretch")


tab_fund, tab_daily = st.tabs(["📈 Haftalık Fon Kasası", "⚡ Günlük İşlem Kasası"])

with tab_fund:
    _render_bucket("FUND", "Haftalık Fon Kasası (20.000 TL başlangıç)", _fund_price_lookup, "TEFAS fon kodu (örn. AFA)")

with tab_daily:
    _render_bucket("DAILY", "Günlük İşlem Kasası (10.000 TL başlangıç)", _stock_price_lookup, "BIST hisse kodu (örn. THYAO)")

st.divider()
st.subheader("💾 Veri Yedekleme")
st.caption(
    "Bu paneli bir bulut ortamında (ör. Streamlit Community Cloud) çalıştırıyorsanız dosya sistemi "
    "kalıcı değildir — uygulama yeniden başladığında portföy verisi sıfırlanabilir. Düzenli olarak "
    "yedek indirip saklayın; gerektiğinde geri yükleyin."
)
col_dl, col_ul = st.columns(2)
with col_dl:
    if db.DB_PATH.exists():
        with open(db.DB_PATH, "rb") as f:
            st.download_button(
                "⬇️ Portföy Yedeği İndir (.db)",
                f.read(),
                file_name=f"portfolio_{dt.date.today().isoformat()}.db",
            )
with col_ul:
    uploaded = st.file_uploader("⬆️ Yedekten Geri Yükle (.db)", type=["db"])
    if uploaded is not None and st.button("Geri yüklemeyi onayla (mevcut veriyi değiştirir)"):
        with open(db.DB_PATH, "wb") as f:
            f.write(uploaded.getbuffer())
        st.success("Geri yükleme tamamlandı.")
        st.cache_data.clear()
        st.rerun()
