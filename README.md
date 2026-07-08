# Fon & BIST Hisse Analiz Sistemi

Haftalık TEFAS fon analizi ve günlük BIST hisse taraması için yerel bir Streamlit paneli.
Yalnızca bilgilendirme/analiz amaçlıdır, yatırım tavsiyesi değildir.

## Kurulum

```
cd fon_sistemi
pip install -r requirements.txt
```

## Çalıştırma

```
streamlit run app.py
```

Tarayıcıda `http://localhost:8501` açılır. Sol menüden:

- **Haftalık Fon Analizi** — her Pazartesi kullanın, "Verileri Yenile" ile güncel TEFAS verisini çekin.
- **Günlük İşlem Analizi** — her sabah kullanın, BIST hisseleri için teknik tarama.
- **Portföyüm** — gerçekleştirdiğiniz alım/satımları elle kaydedin, bakiye ve K/Z otomatik hesaplanır.

## Kısıtlar

- Fon içindeki spesifik hisse senedi ağırlıkları (TEFAS ücretsiz API'sinde yok) — yalnızca varlık sınıfı
  dağılımı (%hisse senedi, %tahvil, %döviz vb.) gösterilir.
- Midas'a veya başka bir aracı kuruma otomatik bağlantı/emir gönderimi yoktur.
- Veriler yalnızca ücretsiz/genel kaynaklardan (TEFAS, Yahoo Finance) çekilir.

## Veri dosyası

Portföy verileri `portfolio/portfolio.db` (SQLite) dosyasında tutulur, silmediğiniz sürece kalıcıdır.
