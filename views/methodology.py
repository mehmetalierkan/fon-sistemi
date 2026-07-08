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
