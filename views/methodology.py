"""Sistemin fon/hisse degerlendirirken kullandigi kriterlerin detayli anlatimi."""
import streamlit as st

from ui import gradient_title

gradient_title("Nasıl Değerlendiriyoruz?", "🧭")
st.caption("Bu sayfa, diğer sayfalardaki her sayının ve önerinin nereden geldiğini şeffafça açıklar.")

st.markdown("## 📈 Haftalık Fon Analizi Kriterleri")

st.markdown("#### 1) Getiri hesaplama")
st.markdown(
    """
TEFAS'ın yayınladığı günlük **NAV (birim pay fiyatı)** üzerinden 4 dönem için getiri hesaplanır:
**1 hafta, 1 ay, 3 ay, 6 ay.** Her dönem için "bugünkü fiyat / dönem başındaki fiyat − 1" formülü kullanılır.
Tüm fon evreni (~2000 fon) için bu hesap birkaç toplu API çağrısıyla yapılır, fon başına ayrı çağrı gerekmez.
"""
)

st.markdown("#### 2) Volatilite (risk) ölçümü")
st.markdown(
    """
En yüksek getirili ~30 fon kısa listeye alınır ve bu fonların **son 3 aylık günlük NAV geçmişi** çekilerek
günlük getirilerin standart sapması hesaplanır, ardından **yıllıklandırılır** (×√252). Bu, fonun ne kadar
inişli-çıkışlı olduğunu gösterir — düşük volatilite = daha istikrarlı seyir.
"""
)

st.markdown("#### 3) Getiri / Volatilite oranı (asıl sıralama kriteri)")
st.markdown(
    """
Öneriler **getiri ÷ volatilite** oranına göre sıralanır — yani "bu fon riskine göre ne kadar getiri
sağlıyor?" sorusuna cevap arar. Sadece yüksek getirili değil, **getirisi risklerine oranla yüksek** fonlar
öne çıkar. Bu, iki fon aynı getiriyi sağlasa bile daha az iniş-çıkış yaşayanı tercih eder.
"""
)

st.markdown("#### 4) Kategori persentili")
st.markdown(
    """
Her fon, TEFAS'taki fon unvanına bakılarak bir **kategoriye** atanır (Hisse Senedi, Katılım, Para
Piyasası, Karma/Değişken, Borçlanma Araçları, Serbest, Endeks, Kıymetli Maden, Fon Sepeti, Gayrimenkul,
Girişim Sermayesi, Diğer). Ardından fonun 1 aylık getirisi, **kendi kategorisindeki diğer fonlarla**
karşılaştırılıp bir persentil (yüzdelik dilim) hesaplanır — "%92'sinden iyi performans gösterdi" gibi.
"""
)

st.markdown("#### 5) Sektör / Tema (şemsiye) etiketi")
st.markdown(
    """
Kategorinin yanında, fonun **hangi sektöre/temaya odaklandığına** dair ek bir etiket daha
gösterilir (ör. Bankacılık/Finans, Teknoloji, Enerji, Amerika Hisse Senedi, Küresel/Yabancı, Sağlık,
Gayrimenkul/İnşaat, Temettü Odaklı, Sürdürülebilirlik/ESG vb.). Bu etiket sayesinde farklı sektörlere
dağıtılmış bir **şemsiye portföy** kurgulayabilir, aynı sektöre aşırı yüklenip yüklenmediğinizi
görebilirsiniz.

**Önemli sınır:** Bu etiket **fon unvanındaki anahtar kelimelerden** tahmin edilir (ör. "AK PORTFÖY
AMERİKA YABANCI HİSSE SENEDİ FONU" → *Amerika Hisse Senedi*). TEFAS'ın ücretsiz API'si fonun gerçek
portföyündeki sektörel dağılımı vermez — bu yüzden fon adı sektörünü açıkça belirtmiyorsa etiket
"Genel / Karma" olarak görünür ve bu, fonun sektörsüz olduğu anlamına gelmez, sadece isimden tahmin
edilemediği anlamına gelir.
"""
)

st.markdown("#### 6) Varlık dağılımı")
st.markdown(
    """
TEFAS'ın herkese açık API'si her fon için **varlık sınıfı bazında** dağılım verir: %hisse senedi,
%devlet tahvili, %eurobond, %döviz mevduatı, %repo, %kıymetli maden vb. (50'den fazla kategori).
Gerekçe metninde en büyük 3 bileşen gösterilir, grafiklerde en büyük 7 bileşen + "Diğer" olarak özetlenir.

**Önemli sınır:** Bu API, fon içindeki **spesifik hisse senedi isimlerini/ağırlıklarını** (ör. "%5 THYAO,
%3 ASELS") vermez — böyle bir kırılım yalnızca fonu yöneten portföy yönetim şirketinin aylık PDF
bültenlerinde bulunur ve fon bazında formatı farklı olduğu için sistematik/otomatik olarak çekilemez.
"""
)

st.markdown("#### 7) Güvenilirlik filtresi (veri anomalisi koruması)")
st.markdown(
    """
Küçük/yeni/düşük likiditeli fonlarda bazen gerçekçi olmayan getiri sıçramaları görülür (ör. tek bir
ayda %850 gibi). Bunları elemek için öneri listesine girecek fonlarda şu şartlar aranır:

- Fon büyüklüğü ≥ **10 milyon TL**
- Yatırımcı sayısı ≥ **20**
- 1 aylık getiri mutlak değeri ≤ **%100**, 3 aylık ≤ **%200**

Bu şartları sağlamayan fonlar tam karşılaştırma tablosunda görünmeye devam eder, ama öneri kartlarında
önerilmez.
"""
)

st.divider()
st.markdown("## ⚡ Günlük İşlem Analizi Kriterleri (BIST Hisseleri)")

st.markdown("#### İzleme listesi")
st.markdown("30 likit BIST30/BIST100 hissesinden oluşan sabit bir liste taranır (Yahoo Finance üzerinden).")

st.markdown("#### Sinyal bileşenleri")
st.markdown(
    """
| Bileşen | Nasıl hesaplanır | Ne anlama gelir |
|---|---|---|
| **Trend** | Kapanış > SMA20 ve SMA20 > SMA50 | Kısa vadeli fiyat trendi yukarı mı? |
| **RSI(14)** | Son 14 günün ortalama kazanç/kayıp oranından | 45–65 arası "sağlıklı" kabul edilir; >70 aşırı alım, <30 aşırı satım |
| **Hacim oranı** | Günün hacmi ÷ 20 günlük ortalama hacim | 1.3x üzeri "ilgi artışı" olarak yorumlanır |
| **Momentum** | Son 5 işlem gününün toplam getirisi | Kısa vadeli ivme |
"""
)

st.markdown("#### Skor formülü")
st.code(
    "skor = (2.0 eğer trend yukarıysa) + (RSI 55'e yakınlık puanı × 1.5) "
    "+ (min(hacim oranı, 3.0) × 0.5) + (pozitif momentum × 0.1)",
    language="text",
)
st.markdown(
    "En yüksek skorlu 5 hisse 'Bugünün Öne Çıkan Adayları' olarak gösterilir. "
    "Girdiğiniz günlük bütçeyle kaç adet alınabileceği otomatik hesaplanır."
)

st.divider()
st.markdown("## 🌂 Şemsiye Portföy Oluşturucu Kriterleri")

st.markdown("#### 1) Sektör/tema eşleştirme kaynakları")
st.markdown(
    """
Girdiğiniz her sektör/tema başlığı için iki aday havuzu oluşturulur:

- **Fonlar**: Fonun **unvanındaki anahtar kelimelerden** tahmin edilen tema etiketi kullanılır
  (Haftalık Fon Analizi'ndeki Sektör/Tema etiketiyle aynı mekanizma). *Yenilenebilir Enerji* seçilirse
  fon adında "YENİLENEBİLİR", "TEMİZ ENERJİ", "GÜNEŞ", "RÜZGAR" gibi kelimeler aranır; *Perakende / Gıda*
  seçilirse fon tarafında "Tarım / Gıda" temasıyla eşleştirilir.
- **Hisseler**: İzleme listesindeki her hisse için **elle hazırlanmış sabit bir sektör haritası**
  kullanılır (ör. GARAN → Bankacılık / Finans, LOGO → Teknoloji, AYDEM/GWIND → Yenilenebilir Enerji).

**Önemli sınır:** Fon eşleşmesi isim bazlı bir **tahmindir** — TEFAS'ın ücretsiz API'si fonun gerçek
portföyündeki sektörel dağılımı vermez. Hisse eşleşmesi de resmi bir sınıflandırma değil, elle atanmış
bir haritadır. *Ulaştırma*, *Telekom* ve *Holding* başlıkları fon adlarından tahmin edilemediği için bu
başlıklarda yalnızca hisse önerilir; bir başlıkta uygun/likit hisse yoksa yalnızca fon önerilir ve bu
durum size açıkça bildirilir.
"""
)

st.markdown("#### 2) Yüzde normalizasyonu")
st.markdown(
    """
Girdiğiniz hedef yüzdelerin toplamı 100 değilse, oranlar korunarak otomatik olarak **%100'e normalize
edilir** ve sayfada bir uyarıyla belirtilir. Aynı sektör birden fazla satırda girilirse yüzdeleri toplanır.
Hiç adayı bulunamayan bir sektör portföyden çıkarılır ve yüzdesi kalan sektörlere oransal dağıtılır.
"""
)

st.markdown("#### 3) Aday seçimi ve skorlar")
st.markdown(
    """
Her sektör içinde adaylar mevcut sayfaların skorlama mantığıyla sıralanır:

- **Fonlar**: Önce güvenilirlik filtresi uygulanır (büyüklük ≥ 10 mn TL, yatırımcı ≥ 20, anomali
  getiriler hariç — Haftalık Fon Analizi ile aynı). Ardından en yüksek getirili adayların 3 aylık
  volatilitesi hesaplanıp **getiri ÷ volatilite** oranına göre sıralanır.
- **Hisseler**: Günlük İşlem Analizi'ndeki **teknik skor** kullanılır (trend + RSI + hacim + momentum).

Sektör içinde birden fazla öneri gerekiyorsa çeşitlilik için **en iyi fon ile en iyi hisse dönüşümlü**
seçilir; yalnızca tek tür aday varsa o türün en iyileri alınır. Aynı enstrüman iki sektörde birden önerilmez.
"""
)

st.markdown("#### 4) 5–10 öneri kısıtı")
st.markdown(
    """
Toplam öneri sayısı her zaman **5 ile 10 arasında** tutulur. Hedef sayı `2 × sektör sayısı` olarak
başlar ve 5–10 bandına sıkıştırılır:

- **10'dan fazla sektör** girilirse en yüksek yüzdeli 10 sektör tutulur, kalanlar uyarıyla çıkarılır.
- **1–2 sektör** girilirse her sektörden birden fazla enstrüman (sektör başına en fazla 5) alınarak
  toplam 5'e tamamlanır.
- Ek öneri hakları, yüzdesi yüksek sektörlere öncelik verilerek dağıtılır. Uygun aday sayısı yetersizse
  toplam 5'in altında kalabilir; bu durum açıkça bildirilir.
"""
)

st.markdown("#### 5) Tutar dağıtımı")
st.markdown(
    """
Her sektörün payı `toplam bütçe × normalize yüzde` olarak hesaplanır; sektör içinde birden fazla öneri
varsa bu tutar öneriler arasında **eşit bölünür**. Hisseler için ayrılan tutarla kaç adet alınabileceği
güncel fiyattan hesaplanıp gösterilir.
"""
)

st.divider()
st.markdown("## 🏆 Sektörel Performans Kriterleri")
st.markdown(
    """
Bu sayfa iki ayrı sıralama üretir; ikisi de **bu an itibariyle** çekilen verinin anlık görüntüsüdür
(fon evreni 1 saat, hisse taraması 15 dakika önbelleklenir, "Verileri Yenile" ile güncellenir):

- **Fon Temaları**: Güvenilirlik filtresini geçen fonlar tema etiketine göre gruplanır; her tema için
  fon sayısı, **ortalama 1 ay / 3 ay getirisi** ve ortalama getiri skoru (1a/3a/6a getirilerinin
  ortalaması) hesaplanır. Sıralama ortalama getiri skoruna göredir; temanın en iyi fonu da gösterilir.
- **Hisse Sektörleri**: İzleme listesindeki hisseler sabit sektör haritasına göre gruplanır; her sektör
  için hisse sayısı, **ortalama teknik skor** ve ortalama 5 günlük momentum hesaplanır. Sıralama
  ortalama teknik skora göredir; sektörün en yüksek skorlu hissesi de gösterilir.

**Önemli sınır:** Tema/sektör etiketlerinin kaynağı Şemsiye Portföy sayfasıyla aynıdır (fonlarda isim
bazlı tahmin, hisselerde elle hazırlanmış harita). Geçmiş performans sıralaması geleceğe dair garanti
vermez; bu sayfa yatırım tavsiyesi değildir.
"""
)

st.divider()
st.markdown("## 💼 Portföy Hesaplamaları")
st.markdown(
    """
- **Ortalama maliyet yöntemi**: Her alışta, o ana kadarki adet ve maliyet ağırlıklı ortalanır.
- **Gerçekleşmiş K/Z**: Satış anında (satış fiyatı − o ana kadarki ortalama maliyet) × satılan adet.
- **Gerçekleşmemiş K/Z**: Açık pozisyonlar için (güncel fiyat − ortalama maliyet) × elde tutulan adet.
"""
)

st.divider()
st.markdown("## 🔎 Veri Kaynakları ve Sınırlamalar")
st.markdown(
    """
- **TEFAS** (tefas.gov.tr) — resmi olmayan ama herkese açık JSON API'si; fon fiyat geçmişi, getiri
  sıralaması ve varlık dağılımı için kullanılır.
- **Yahoo Finance** chart API — BIST hisseleri için fiyat/hacim geçmişi.
- Sistem **hiçbir aracı kuruma (Midas dahil) otomatik bağlanmaz**, emir göndermez. Sadece analiz ve
  öneri üretir; gerçekleştirdiğiniz işlemleri Portföyüm sayfasından elle girmeniz gerekir.
- Bu sistem **yatırım tavsiyesi değildir**; tüm kararlar ve sorumluluk size aittir.
"""
)
