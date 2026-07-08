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
    "En yüksek skorlu 5 hisse 'Bugünün Öne Çıkan Adayları' olarak gösterilir. Bütçe artık bu sayfada elle "
    "girilmez; **Portföyüm** sayfasındaki Günlük İşlem Kasası bakiyeniz otomatik kullanılır ve kaç adet "
    "alınabileceği buna göre hesaplanır."
)

st.markdown("#### Ne kadar süre için geçerli?")
st.markdown(
    """
Bu bir **kısa vadeli teknik okumadır** — RSI, hacim oranı ve momentum gibi bileşenler gün içinde hızla
değişebilir. Sinyal tipik olarak birkaç gün ile 2-3 hafta arasında anlamlıdır; pozisyonu en az haftada
bir (idealde sayfa her güncellendiğinde) tekrar değerlendirmeniz önerilir. Şirket haberleri, bilanço
açıklamaları gibi temel/haber bazlı gelişmeler bu teknik skora dahil değildir.
"""
)

st.markdown("#### Mum (candlestick) grafiği nasıl okunur?")
st.markdown(
    """
Hisse Detayı bölümündeki grafik bir **mum grafiğidir**: her mum bir işlem gününü temsil eder.
Gövde (kalın kısım) açılış-kapanış aralığını, fitil (ince çizgiler) günün en yüksek/en düşük fiyatını
gösterir. 🟢 Yeşil mum kapanışın açılıştan yüksek (gün yükselişle kapanmış), 🔴 kırmızı mum ise düşük
(gün düşüşle kapanmış) olduğu anlamına gelir. Sayfanın altındaki **"🕯️ Bu mum grafiği nasıl okunur?"**
bölümünde de aynı açıklama yer alır.
"""
)

st.divider()
st.markdown("## 🌂 Şemsiye Portföy Oluşturucu Kriterleri")

st.markdown("#### 0) Sektör Önerisi Sihirbazı (soru-cevapla hedef belirleme)")
st.markdown(
    """
Hangi sektörlere/temalara ne kadar pay ayıracağınıza karar veremiyorsanız, hedef tablonun üstündeki
**"🧙 Sektör Hedeflerini Belirlemekte Zorlanıyor musunuz?"** bölümünü açıp şu soruları cevaplayabilirsiniz:

- **İlgilendiğiniz sektör/temalar** (çoklu seçim) — öneri SADECE burada seçtiğiniz sektörler arasında
  dağıtılır, seçmediğiniz bir sektör asla önerilmez.
- **Yatırım vadeniz** (Kısa / Orta / Uzun vadeli)
- **Risk toleransınız** (Düşük / Orta / Yüksek)
- **Önceliğiniz** (İstikrar / Dengeli / Büyüme)

Sistem bu 3 cevaptan **1.0 (düşük risk) - 3.0 (yüksek risk)** ölçeğinde bir "hedef risk seviyesi"
hesaplar. Her sektöre önceden atanmış kabaca bir risk/oynaklık etiketi vardır (ör. Teknoloji/Yenilenebilir
Enerji/Girişim Sermayesi = Yüksek; Kıymetli Maden/Temettü Odaklı/Telekom = Düşük; çoğu diğer sektör =
Orta). Seçtiğiniz sektörlerden, risk etiketi hedef seviyenize **daha yakın olanlar orantılı olarak daha
fazla pay** alır — ama seçtiğiniz hiçbir sektör tamamen elenmez. Sonuç otomatik olarak aşağıdaki tabloyu
doldurur; oradan dilediğiniz gibi düzenlemeye devam edebilirsiniz.

**Önemli sınır:** Bu, kişiselleştirilmiş bir finansal tavsiye motoru değildir — sabit, şeffaf bir kural
tabanlı eşleştirmedir (risk etiketi + cevaplarınız → ağırlık). Sektör risk etiketleri kabaca bir
genellemedir, her fonun/hissenin gerçek riskini yansıtmayabilir.
"""
)

st.markdown("#### 1) Fon ve hisse şemsiyeleri AYRI oluşturulur")
st.markdown(
    """
Girdiğiniz sektör/tema dağılımı **ortak** bir girdidir, ama sonuçta **iki bağımsız portföy** üretilir —
kendi bütçesi, kendi 5-10 enstrüman kısıtı ve kendi tablosu olan bir **Fon Şemsiyesi** ve bir **Hisse
Şemsiyesi**. Fon bütçesi varsayılan olarak Portföyüm'deki Haftalık Fon Kasası bakiyenizden, hisse bütçesi
Günlük İşlem Kasası bakiyenizden gelir (isterseniz değiştirebilirsiniz) — bu, sistemin zaten takip ettiği
iki ayrı kasa mantığıyla birebir uyumludur.

Her sektör/tema başlığı için iki ayrı aday havuzu değerlendirilir:

- **Fonlar**: Fonun **unvanındaki anahtar kelimelerden** tahmin edilen tema etiketi kullanılır
  (Haftalık Fon Analizi'ndeki Sektör/Tema etiketiyle aynı mekanizma). *Yenilenebilir Enerji* seçilirse
  fon adında "YENİLENEBİLİR", "TEMİZ ENERJİ", "GÜNEŞ", "RÜZGAR" gibi kelimeler aranır; *Perakende / Gıda*
  seçilirse fon tarafında "Tarım / Gıda" temasıyla eşleştirilir.
- **Hisseler**: İzleme listesindeki her hisse için **elle hazırlanmış sabit bir sektör haritası**
  kullanılır (ör. GARAN → Bankacılık / Finans, LOGO → Teknoloji, AYDEM/GWIND → Yenilenebilir Enerji).

**Önemli sınır:** Fon eşleşmesi isim bazlı bir **tahmindir** — TEFAS'ın ücretsiz API'si fonun gerçek
portföyündeki sektörel dağılımı vermez. Hisse eşleşmesi de resmi bir sınıflandırma değil, elle atanmış
bir haritadır. *Ulaştırma*, *Telekom* ve *Holding* başlıkları fon adlarından tahmin edilemediği için bu
başlıklarda Fon Şemsiyesi'nde öneri çıkmaz (yalnızca Hisse Şemsiyesi'nde); bir başlıkta uygun/likit hisse
yoksa Hisse Şemsiyesi'nde o başlık boş kalır — her iki durum da açıkça bildirilir.
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
Her sektör içinde, kendi türünün adayları mevcut sayfaların skorlama mantığıyla sıralanır:

- **Fon Şemsiyesi**: Önce güvenilirlik filtresi uygulanır (büyüklük ≥ 10 mn TL, yatırımcı ≥ 20, anomali
  getiriler hariç — Haftalık Fon Analizi ile aynı). Ardından en yüksek getirili adayların 3 aylık
  volatilitesi hesaplanıp **getiri ÷ volatilite** oranına göre sıralanır.
- **Hisse Şemsiyesi**: Günlük İşlem Analizi'ndeki **teknik skor** kullanılır (trend + RSI + hacim +
  momentum).

Sektör içinde birden fazla öneri gerekiyorsa o türün en iyilerinden sırayla alınır. Aynı enstrüman aynı
şemsiye içinde iki sektörde birden önerilmez.
"""
)

st.markdown("#### 4) 5–10 öneri kısıtı")
st.markdown(
    """
Fon Şemsiyesi ve Hisse Şemsiyesi **her biri kendi içinde** 5 ile 10 enstrüman arasında tutulur (biri 7
fon, diğeri 9 hisse önerebilir — bağımsız hesaplanır). Hedef sayı `2 × sektör sayısı` olarak başlar ve
5–10 bandına sıkıştırılır:

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
Bu sayfa üç ayrı sıralama üretir; hepsi **bu an itibariyle** çekilen verinin anlık görüntüsüdür
(fon evreni 1 saat, hisse taramaları 15 dakika önbelleklenir, "Verileri Yenile" ile güncellenir):

- **Fon Temaları**: Güvenilirlik filtresini geçen fonlar tema etiketine göre gruplanır; her tema için
  fon sayısı, **ortalama 1 ay / 3 ay getirisi** ve ortalama getiri skoru (1a/3a/6a getirilerinin
  ortalaması) hesaplanır. Sıralama ortalama getiri skoruna göredir; temanın en iyi fonu da gösterilir.
- **BIST Hisse Sektörleri**: İzleme listesindeki hisseler sabit sektör haritasına göre gruplanır; her
  sektör için hisse sayısı, **ortalama teknik skor** ve ortalama 5 günlük momentum hesaplanır.
- **ABD Sektörleri**: Aynı fonksiyon (`umbrella.stock_sector_performance`) ABD izleme listesi ve
  `US_SECTORS` haritasıyla yeniden çalıştırılır — mantık BIST ile birebir aynıdır, sadece evren farklıdır.

**Önemli sınır:** Tema/sektör etiketlerinin kaynağı Şemsiye Portföy sayfasıyla aynıdır (fonlarda isim
bazlı tahmin, hisselerde elle hazırlanmış harita). Geçmiş performans sıralaması geleceğe dair garanti
vermez.
"""
)

st.divider()
st.markdown("## 🇺🇸 ABD Borsası Kriterleri")
st.markdown(
    """
Büyük/likit ABD hisseleri (ör. AAPL, MSFT, NVDA, JPM) için **⚡ Günlük İşlem Analizi ile birebir aynı**
teknik tarama formülü kullanılır (Trend + RSI(14) + Hacim oranı + 5 günlük Momentum → skor), aynı kısa
vadeli (birkaç gün - birkaç hafta) geçerlilik süresi ve aynı mum grafiği okuma mantığı geçerlidir. Tek
fark verinin USD cinsinden olması ve evrenin ABD hisseleri olmasıdır. Bütçe burada da elle girilmez;
Portföyüm'deki Günlük İşlem Kasası bakiyeniz güncel Dolar/TL kuruyla USD'ye çevrilerek otomatik kullanılır.
Ayrıca S&P 500, Nasdaq Composite ve Dow Jones Endüstri endeksleri karşılaştırma amacıyla gösterilir.
Sektör etiketleri (ör. Teknoloji, Bankacılık/Finans) BIST hisselerindeki gibi elle hazırlanmış sabit bir
haritadan gelir.
"""
)

st.divider()
st.markdown("## 💱 Döviz & Kıymetli Maden Kriterleri")
st.markdown(
    """
Dolar/Euro/Sterlin paritesi ile ons altın/gümüş fiyatları **tek bir siteye dayanmaz** — iki bağımsız
kaynak birlikte değerlendirilir:

- **Birincil kaynak — Yahoo Finance (teknik göstergeler):** Trend (SMA20/SMA50) + RSI(14) + 5 günlük
  Momentum.
- **İkincil kaynak — bağımsız çapraz kontrol:** Döviz paritelerinde **Frankfurter.app** (Avrupa Merkez
  Bankası referans kurları) üzerinden hesaplanan son ~10 iş günlük bağımsız momentum; kıymetli madenlerde
  ise **GLD/SLV ETF'lerinin** (altın/gümüşü farklı bir piyasa mekanizmasıyla izleyen borsa yatırım
  fonları) fiyat hareketi.

İki kaynak aynı yönü işaret ediyorsa sinyal güçlenir (**Al Yönlü**/**Sat Yönlü**); çelişiyorsa sinyal
**Nötr**'e çekilir ve bu sayfada açıkça belirtilir. Her enstrüman için ayrıca:

- **Sistemin görüşü:** iki kaynağın birleşik okumasına dayanan, açıkça gerekçelendirilmiş kısa bir yorum
  (kesin bir alım-satım talimatı değildir).
- **Ne kadar süre tutulmalı?** Bu sinyal kısa vadelidir (birkaç gün - 2 hafta); uzun vadeli tasarruf
  amaçlı (ör. yıllar içinde altın biriktirme) tutuluyorsa önemi azalır.

Gram altın/gümüş TL karşılığı, ons fiyatının (USD) güncel Dolar/TL kuruyla çarpılıp 31.1034768'e
(1 ons = bu kadar gram) bölünmesiyle hesaplanır.
"""
)

st.divider()
st.markdown("## 🏛️ Analist Önerileri Kriterleri")
st.markdown(
    """
Bu sayfa kendi teknik skorlama sistemimizi değil, **farklı yatırım kuruluşlarının (sell-side
analistlerin)** o hisse için verdiği al/sat görüşlerinin özetini gösterir — Yahoo Finance'in topladığı
konsensus verisi kullanılır:

- **Hangi kurumlardan veri geliyor?** Toplam Güçlü Al/Al/Tut/Sat/Güçlü Sat sayıları Yahoo'nun
  agregasyonudur (bu sayılarda tek tek hangi bankalar olduğu belirtilmez). Ancak her hissenin altındaki
  **"Son Hareket Eden Kurumlar"** listesi Yahoo'nun `upgradeDowngradeHistory` verisinden gelen **gerçek
  kurum adlarını** (ör. Morgan Stanley, JPMorgan, Goldman Sachs, Evercore ISI gibi), hareket tarihini,
  eski/yeni dereceyi ve o kurumun güncel hedef fiyatını gösterir.
- **Konsensus Skoru**: 1.0 (Güçlü Al) ile 5.0 (Güçlü Sat) arasında, analist görüşlerinin ortalaması.
  Düşük skor = daha olumlu konsensus. Sıralama bu skora göre (düşükten yükseğe) yapılır.
- **Analist dağılımı**: Güçlü Al / Al / Tut / Sat / Güçlü Sat kategorilerinde kaç analist görüş
  bildirdiği.
- **Hedefe göre potansiyel**: Analistlerin ortalama hedef fiyatının güncel fiyata göre yüzde farkı.
- **Sistemin görüşü:** Konsensus + hedef fiyat potansiyelini birleştiren kısa bir yorum; teknik
  sinyallerle çelişebileceği (farklı zaman ufuklarına baktıkları için) açıkça belirtilir.
- **Ne kadar süre için geçerli?** Analist hedef fiyatları tipik olarak **12 aylık** bir ufku yansıtır —
  bu, teknik tarama sayfalarındaki günlük/haftalık sinyallerden çok daha uzun vadelidir ve genellikle
  çeyreklik bilanço dönemlerinde güncellenir.

**Önemli sınır:** Bu veri, herkese açık ama belgelendirilmemiş bir Yahoo Finance uç noktasından gelir;
özellikle küçük/az takip edilen BIST hisselerinde analist kapsaması bulunmayabilir — bu durumda hisse
tabloda hiç görünmez (sıfır olarak değil, eksik veri olarak ele alınır).
"""
)

st.divider()
st.markdown("## ⭐ Ana Sayfa \"Öne Çıkanlar\" ve Bütçe Yönetimi")
st.markdown(
    """
Ana sayfadaki Fonlar / BIST Hisseleri / ABD Hisseleri / Döviz-Altın sekmeleri, **yeni bir kriter
üretmez** — her biri kendi sayfasındaki sıralamanın ilk 3 sonucunu gösterir (yukarıdaki ilgili bölümlere
bakın).

**Bütçeler sadece Portföyüm sayfasında gösterilir ve düzenlenir** (ana sayfada artık bütçe bilgisi yok,
tekrar bilgi göstermenin bir anlamı olmadığı için kaldırıldı). Her kasanın (Haftalık Fon / Günlük İşlem)
altındaki **"🎯 Nakit Bütçeyi Güncelle"** bölümünden bakiyeyi doğrudan değiştirebilirsiniz; bu değer,
diğer tüm sayfalardaki (Günlük İşlem Analizi, ABD Borsası, Şemsiye Portföy Oluşturucu) varsayılan bütçe
olarak otomatik kullanılır — o sayfalarda ayrıca bir bütçe girişi yoktur, çünkü aynı bilginin birden
fazla yerde tekrar girilmesinin bir anlamı yok.
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
- **Yahoo Finance** chart API — BIST/ABD hisseleri, döviz paritesi ve kıymetli maden futures'ları için
  fiyat/hacim geçmişi.
- **Yahoo Finance** quoteSummary uç noktası (crumb/çerez ile) — Analist Önerileri sayfasındaki sell-side
  konsensus verisi için.
- Sistem **hiçbir aracı kuruma (Midas dahil) otomatik bağlanmaz**, emir göndermez. Sadece analiz ve
  öneri üretir; gerçekleştirdiğiniz işlemleri Portföyüm sayfasından elle girmeniz gerekir.
"""
)
