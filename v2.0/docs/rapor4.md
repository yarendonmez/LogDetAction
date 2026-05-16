Aşağıdaki metni rapora **“Balanced Fine-Tuning Deneyi ve Hata Analizi”** başlığıyla ekleyebilirsin.

---

# Balanced Fine-Tuning Deneyi ve Hata Analizi

## 1. Deneyin Amacı

Önceki aşamada classifier-only QLoRA adapter, rastgele seçilen 100 örneklik test üzerinde oldukça yüksek performans göstermiştir. Bu testte model %99 3-class accuracy ve %100 attack detection accuracy elde etmiştir. Ancak bu 100 örneklik test setinde suspicious sınıfı yalnızca bir örnekle temsil edilmiştir. Bu nedenle modelin suspicious sınıfını gerçekten öğrenip öğrenmediği bu testle güvenilir şekilde ölçülememiştir.

Bu eksikliği gidermek amacıyla balanced evaluation yapılmıştır. Balanced evaluation kapsamında test setinden her sınıftan eşit sayıda örnek seçilmiştir:

```text
benign: 100
suspicious: 100
malicious: 100
```

Bu testin amacı, modelin her sınıf üzerindeki performansını daha adil biçimde ölçmek ve özellikle suspicious sınıfındaki davranışını analiz etmektir.

İlk balanced evaluation sonucunda modelin benign ve malicious sınıflarında güçlü, ancak suspicious sınıfında başarısız olduğu görülmüştür. Bu testte model 100 suspicious örneğin tamamını benign olarak sınıflandırmıştır. Buna karşın malicious sınıfında 99/100 başarı elde etmiş ve attack detection accuracy %99.67 olarak ölçülmüştür. 

Bu sonuç, modelin saldırı tespiti açısından güçlü olduğunu; ancak üç sınıflı sınıflandırmada suspicious sınıfını öğrenemediğini göstermiştir.

---

## 2. İlk Balanced Evaluation Bulgusu

İlk classifier-only model, dengeli 300 örneklik test setinde aşağıdaki sonucu vermiştir:

| Metrik                    |            Sonuç |
| ------------------------- | ---------------: |
| 3-Class Accuracy          | 199/300 = %66.33 |
| Attack Detection Accuracy | 299/300 = %99.67 |
| Average Inference Time    |        1.217 sec |
| Median Inference Time     |        1.358 sec |

Confusion matrix sonucu şu şekildedir:

| True \ Pred | benign | suspicious | malicious |
| ----------- | -----: | ---------: | --------: |
| benign      |    100 |          0 |         0 |
| suspicious  |    100 |          0 |         0 |
| malicious   |      1 |          0 |        99 |

Bu sonuçta model benign sınıfını tamamen doğru sınıflandırmış, malicious sınıfında çok yüksek başarı elde etmiş, ancak suspicious sınıfındaki tüm örnekleri benign olarak tahmin etmiştir. Per-class metriklerde suspicious precision, recall ve F1 değerlerinin tamamı 0 olarak ölçülmüştür. 

Bu durum, modelin suspicious sınıfını yeterince öğrenmediğini göstermiştir. Bunun temel nedeni, önceki classifier-only eğitiminde kullanılan 1000 örneklik alt kümede suspicious sınıfının çok az temsil edilmesidir. Eğitim alt kümesinde benign ve malicious sınıfları yüksek sayıda bulunurken suspicious sınıfı yalnızca sınırlı sayıda örnekle modele gösterilmiştir. Bu nedenle model, HDFS suspicious/anomaly örüntülerini öğrenmek yerine HDFS loglarını genel olarak benign sınıfına atamayı öğrenmiştir.

---

## 3. Balanced Fine-Tuning Stratejisi

İlk balanced evaluation sonucundan sonra veri dengesizliği problemi tespit edilmiştir. Bu problemi azaltmak amacıyla yeni bir balanced classifier training dataset oluşturulmuştur.

Yeni eğitim setinde her sınıftan eşit sayıda örnek alınmıştır:

```text
benign: 1000
suspicious: 1000
malicious: 1000
```

Toplamda 3000 örnekten oluşan dengeli bir classifier-only training dataset hazırlanmıştır. Bu yaklaşımın amacı, modelin minority class olan suspicious sınıfını daha fazla görmesini sağlamak ve üç sınıflı sınıflandırma performansını iyileştirmektir.

Bu işlem, veri manipülasyonu değil, class imbalance problemini azaltmak için kullanılan standart bir dengeleme yaklaşımıdır. Çünkü önceki eğitimde modelin suspicious sınıfına yeterince maruz kalmadığı ve bu nedenle tüm suspicious örnekleri benign olarak tahmin ettiği gözlemlenmiştir.

Balanced fine-tuning ile modelin şu davranışı kazanması hedeflenmiştir:

```text
HDFS normal logları → benign
HDFS anomaly benzeri loglar → suspicious
Cowrie/honeypot saldırı logları → malicious
```

---

## 4. Balanced Classifier Modelinin Değerlendirilmesi

Balanced training sonrasında yeni classifier adapter, aynı balanced 300 örneklik test seti üzerinde tekrar değerlendirilmiştir. Bu değerlendirmede test seti yine her sınıftan 100 örnek içermiştir. Seçilen test dağılımı şu şekildedir:

```text
benign: 100
suspicious: 100
malicious: 100
```

Balanced-trained classifier modelin değerlendirme sonucu şöyledir:

| Metrik                    |            Sonuç |
| ------------------------- | ---------------: |
| 3-Class Accuracy          | 203/300 = %67.67 |
| Attack Detection Accuracy | 299/300 = %99.67 |
| Average Inference Time    |        0.785 sec |
| Median Inference Time     |        0.780 sec |
| Min Inference Time        |        0.655 sec |
| Max Inference Time        |        1.790 sec |

Bu sonuç, balanced training sonrasında genel 3-class accuracy değerinde çok sınırlı bir artış olduğunu göstermektedir. İlk balanced evaluation’da %66.33 olan 3-class accuracy, balanced training sonrasında %67.67’ye yükselmiştir. Attack detection accuracy ise %99.67 seviyesinde korunmuştur. 

---

## 5. Confusion Matrix Analizi

Balanced-trained modelin confusion matrix sonucu şu şekildedir:

| True \ Pred | benign | suspicious | malicious |
| ----------- | -----: | ---------: | --------: |
| benign      |     18 |         82 |         0 |
| suspicious  |     14 |         86 |         0 |
| malicious   |      1 |          0 |        99 |

Bu tablo, balanced training sonrasında modelin suspicious sınıfını artık öğrenmeye başladığını göstermektedir. İlk classifier-only model suspicious sınıfındaki 100 örneğin 0’ını doğru tahmin ederken, balanced-trained model 100 suspicious örneğin 86’sını doğru şekilde suspicious olarak sınıflandırmıştır. Ancak bu iyileşme, benign sınıfında ciddi bir performans kaybına yol açmıştır. Model 100 benign örneğin yalnızca 18’ini benign olarak tahmin etmiş, 82 benign örneği ise suspicious olarak sınıflandırmıştır. 

Bu sonuç, balanced training’in suspicious recall değerini önemli ölçüde artırdığını, fakat aynı zamanda benign loglar üzerinde false positive oranını yükselttiğini göstermektedir.

---

## 6. Per-Class Metriklerin Yorumu

Balanced-trained modelin sınıf bazlı metrikleri şu şekildedir:

| Sınıf      | Precision | Recall |     F1 |
| ---------- | --------: | -----: | -----: |
| benign     |    0.5455 | 0.1800 | 0.2707 |
| suspicious |    0.5119 | 0.8600 | 0.6418 |
| malicious  |    1.0000 | 0.9900 | 0.9950 |

Bu sonuçlar üç önemli noktayı göstermektedir.

Birincisi, malicious sınıfı yüksek doğrulukla ayrılmaya devam etmektedir. Malicious sınıfı için precision 1.0000, recall 0.9900 ve F1 0.9950 olarak ölçülmüştür. Bu, modelin saldırı loglarını yakalama konusunda güçlü olduğunu göstermektedir.

İkincisi, suspicious sınıfında önemli bir iyileşme sağlanmıştır. Suspicious recall 0’dan 0.86’ya yükselmiştir. Ancak suspicious precision 0.5119 seviyesindedir. Yani model suspicious örnekleri yakalamaya başlamış, fakat çok sayıda benign logu da yanlışlıkla suspicious olarak işaretlemiştir.

Üçüncüsü, benign sınıfında ciddi performans düşüşü yaşanmıştır. Benign recall 0.18’e düşmüştür. Bu, modelin normal HDFS davranışlarını sık sık suspicious olarak yorumladığını göstermektedir. 

---

## 7. Hata Analizi

Yanlış sınıflandırılan örnekler incelendiğinde, modelin özellikle HDFS loglarında benign ve suspicious ayrımında zorlandığı görülmüştür. Yanlış örneklerde sıkça karşılaşılan log tipleri şunlardır:

```text
PacketResponder terminating
Received block
addStoredBlock
allocateBlock
Receiving block
```

Bu loglar HDFS’in normal block yönetimi ve veri aktarımı süreçlerine ait loglardır. Ancak HDFS veri setinde bazı durumlarda bu tür loglar block-level anomaly bağlamında suspicious olarak etiketlenmiştir. Bu nedenle aynı log yapısı bazı örneklerde benign, bazı örneklerde suspicious olarak görülebilmektedir.

Balanced-trained model, suspicious sınıfına daha fazla maruz kaldığı için bu HDFS block operation loglarını daha sık suspicious olarak sınıflandırmaya başlamıştır. Bu da suspicious recall değerini yükseltmiş; fakat benign false positive sayısını artırmıştır. Yanlış sınıflandırma örneklerinde, benign kayıtların `PacketResponder terminating`, `Received block` veya `addStoredBlock` gibi normal HDFS işlemleri olmasına rağmen suspicious olarak tahmin edildiği görülmektedir. 

Bu bulgu, problemin yalnızca model kapasitesiyle ilgili olmadığını; veri etiketleme seviyesinin de önemli olduğunu göstermektedir. HDFS suspicious etiketleri çoğu zaman tek log satırındaki açık bir saldırı göstergesinden değil, ilgili block veya işlem akışının bütünsel anomaliliğinden kaynaklanmaktadır.

---

## 8. Önceki ve Yeni Modelin Karşılaştırılması

İlk classifier-only model ile balanced-trained classifier model karşılaştırıldığında şu tablo ortaya çıkmaktadır:

| Model                       | Test Tipi    | 3-Class Accuracy | Attack Detection Accuracy | Average Inference Time | Ana Problem                                      |
| --------------------------- | ------------ | ---------------: | ------------------------: | ---------------------: | ------------------------------------------------ |
| Classifier-only model       | Balanced 300 |           %66.33 |                    %99.67 |              1.217 sec | Suspicious sınıfını hiç öğrenemedi               |
| Balanced-trained classifier | Balanced 300 |           %67.67 |                    %99.67 |              0.785 sec | Suspicious arttı, benign false positive yükseldi |

İlk model suspicious sınıfını tamamen benign’e atamıştır. Balanced-trained model suspicious sınıfını daha iyi yakalamış, ancak benign sınıfını koruyamamıştır. Dolayısıyla balanced fine-tuning, suspicious recall üzerinde olumlu etki yaratmış; fakat benign ve suspicious arasındaki karar sınırını fazla suspicious lehine kaydırmıştır.

Bu karşılaştırma, yalnızca class balancing uygulamanın tek başına yeterli olmadığını göstermektedir. Çünkü HDFS benign ve suspicious loglarının tek satır düzeyinde semantik olarak çok benzer olması, modelin bu iki sınıfı güvenilir şekilde ayırmasını zorlaştırmaktadır.

---

## 9. Akademik Değerlendirme

Bu deney, proje açısından son derece önemli bir bulgu üretmiştir. Modelin saldırı tespit performansı yüksek kalmasına rağmen üç sınıflı sınıflandırmada benign ve suspicious ayrımı problemli kalmıştır. Bunun temel nedeni, HDFS anomaly etiketlerinin çoğunlukla tek satır log anlamından değil, block-level anomaly bağlamından kaynaklanmasıdır.

Bu nedenle aşağıdaki çıkarım yapılmıştır:

```text
Tek satır log girdisi ile malicious / non-malicious ayrımı yüksek doğrulukla yapılabilir.
Ancak HDFS benign / suspicious ayrımı için tek satır log yeterli olmayabilir.
```

Başka bir ifadeyle, Cowrie tabanlı malicious loglar genellikle açık saldırı davranışı içermektedir. Örneğin komut çalıştırma, SSH fingerprint, TTY oturum bilgisi veya login girişimleri gibi loglar saldırgan davranışına doğrudan işaret edebilir. Buna karşılık HDFS suspicious logları çoğu zaman tek başına normal sistem aktivitesi gibi görünmektedir. Bu nedenle HDFS anomaly tespiti için yalnızca log satırı değil, aynı block ID’ye ait olay dizisi veya daha geniş sistem bağlamı gerekebilir.

Bu durum, projenin kapsamını iki farklı alt probleme ayırmayı gerekli kılmıştır:

```text
1. Attack Detection:
   malicious / non-malicious ayrımı

2. System Anomaly Detection:
   HDFS benign / suspicious ayrımı
```

---

## 10. Mimari Karar

Balanced fine-tuning deneyleri sonucunda sistem mimarisi için şu karar verilmiştir:

```text
LLM-A’nın ana görevi attack detection olacaktır.
```

Yani LLM-A, öncelikli olarak logun saldırı içerip içermediğini hızlı şekilde belirleyecektir:

```text
malicious
non-malicious
```

Üç sınıflı çıktı formatı tamamen terk edilmemiştir; ancak suspicious sınıfı, tek satır log sınıflandırması içinde kesin karar olarak değil, context-aware analiz gerektiren ayrı bir katman olarak ele alınacaktır.

Bu kararın nedeni şudur:

* Malicious sınıfı yüksek doğrulukla yakalanmaktadır.
* Attack detection accuracy her iki balanced testte de %99.67 seviyesinde kalmıştır.
* Suspicious sınıfı dengeli eğitimle öğrenilmeye başlamış, fakat benign false positive oranı ciddi şekilde artmıştır.
* HDFS suspicious etiketleri tek satırdan çok block-level bağlama dayanmaktadır.

Bu nedenle sistemde saldırı tespiti için hızlı classifier-only model kullanılacak, HDFS anomaly/suspicious değerlendirmesi ise ilerleyen aşamada context-aware mekanizma ile geliştirilecektir.

---

## 11. Sonraki Aşama İçin Karar

Bu sonuçlardan sonra LLM-A için iki olası kullanım senaryosu değerlendirilmiştir.

İlk senaryo, classifier-only modelin doğrudan üç sınıflı sınıflandırıcı olarak kullanılmasıdır. Ancak balanced test sonuçları, benign ve suspicious sınıfları arasındaki kararsızlık nedeniyle bu yaklaşımın riskli olduğunu göstermiştir.

İkinci ve daha uygun senaryo, classifier-only modelin attack detection odaklı kullanılmasıdır. Bu senaryoda modelin temel görevi saldırı davranışını yakalamaktır. Suspicious/anomaly sınıfı ise ayrıca incelenecek, özellikle HDFS logları için block ID veya session context bilgisiyle desteklenecektir.

Bu nedenle bir sonraki geliştirme aşamasında şu plan benimsenmiştir:

```text
1. LLM-A classifier modülü attack detection odaklı kullanılacak.
2. Malicious tahminlerinde LLM-B açıklama üretecek.
3. Malicious tahminlerinde LLM-C aksiyon önerisi üretecek.
4. Suspicious/anomaly tespiti için context-aware HDFS analiz modülü ayrıca tasarlanacak.
```

Bu karar, modelin güçlü olduğu alanı kullanmayı, zayıf olduğu alanı ise ayrı bir araştırma ve geliştirme problemi olarak ele almayı sağlamaktadır.

---

## 12. Sonuç

Balanced fine-tuning deneyi, ilk bakışta genel 3-class accuracy açısından sınırlı bir iyileşme sağlamış gibi görünse de proje açısından kritik bir hata analizi üretmiştir. Modelin suspicious sınıfını öğrenebilmesi için dengeli veriyle eğitilmesi gerektiği görülmüş, ancak yalnızca veri dengelemenin benign/suspicious ayrımı için yeterli olmadığı anlaşılmıştır.

Bu aşamada elde edilen en önemli sonuçlar şunlardır:

```text
1. Malicious sınıfı yüksek doğrulukla tespit edilmektedir.
2. Attack detection accuracy %99.67 seviyesinde korunmuştur.
3. Balanced training suspicious recall değerini 0’dan 0.86’ya yükseltmiştir.
4. Ancak benign recall 0.18’e düşmüş ve false positive oranı artmıştır.
5. HDFS benign/suspicious ayrımı tek satır log seviyesinde güvenilir değildir.
6. Suspicious/anomaly analizi için context-aware yaklaşım gereklidir.
```

Bu nedenle proje mimarisinde LLM-A’nın birincil görevi hızlı saldırı tespiti olarak belirlenmiş; açıklama ve öneri modüllerinin yalnızca malicious veya riskli loglar için çalıştırılması kararlaştırılmıştır. HDFS suspicious/anomaly tespiti ise ilerleyen aşamada block-level veya session-level context kullanılarak ayrı bir modül olarak ele alınacaktır.









Şimdi net mimariyi kuruyoruz. Kararımız şu olacak:

# 1. Sınıflandırmayı kim yapacak?

## **LLM-A = `qlora_classifier_test_model`**

Yani şu model:

```text
C:\developer\LogDetAction\v2.0\qlora_classifier_test_model
```

Bunu seçme sebebimiz: hızlı ve attack detection açısından çok güçlü. 100 örneklik testte **%99 3-class accuracy**, **%100 attack detection accuracy** ve **0.777 sn ortalama inference süresi** verdi. 

Balanced model ise suspicious sınıfını öğrenmeye başladı ama benign logları fazla suspicious yapmaya başladı. Balanced modelde suspicious recall %86 oldu ama benign recall %18’e düştü; bu da alarm yorgunluğu riski oluşturur. 

Bu yüzden ana sistemde şimdilik:

```text
Sınıflandırıcı = qlora_classifier_test_model
```

olacak.

Görevi sadece şu:

```text
Log → Label: benign / suspicious / malicious
```

---

# 2. Açıklamayı kim yapacak?

## **LLM-B = `qlora_test_model`**

Yani ilk eğittiğimiz full-output QLoRA adapter:

```text
C:\developer\LogDetAction\v2.0\qlora_test_model
```

Bu model zaten şu formatı öğrenmişti:

```text
Label
Explanation
Recommendation
```

Açıklama üretme konusunda Cowrie/honeypot bağlamını daha iyi öğrendi. Örneğin `Remote SSH version`, `CMD: cat /proc/cpuinfo`, `Closing TTY Log` gibi logları malicious bağlamda yorumlayabildi. Bu modelin 10 örneklik testte **%90 3-class accuracy**, **%100 attack detection accuracy** verdiğini görmüştük; ama her log için açıklama/öneri ürettiği için ortalama süre **12.204 sn** idi. 

Bu yüzden onu her logda çalıştırmayacağız. Sadece LLM-A `malicious` derse açıklama için çağıracağız.

---

# 3. Öneriyi kim üretecek?

## **LLM-C = yine `qlora_test_model`, ama ayrı prompt ile**

İlk aşamada LLM-B ve LLM-C fiziksel olarak aynı adapter’ı kullanabilir:

```text
LLM-B → qlora_test_model + explanation prompt
LLM-C → qlora_test_model + recommendation prompt
```

Yani raporda modüller ayrı olacak:

```text
LLM-A: Classification Module
LLM-B: Explanation Module
LLM-C: Recommendation Module
```

Ama ilk prototipte LLM-B ve LLM-C aynı Mistral tabanlı adapter üzerinden farklı promptlarla çalışacak. Bu mantıklı çünkü 8 GB VRAM’de üç ayrı büyük modeli aynı anda tutmak zor; farklı büyük modeller yüklenirse model değiştirme/VRAM maliyeti artar. Önce güvenli ve çalışan modüler pipeline kuracağız. Daha sonra zaman kalırsa explanation-only ve recommendation-only adapter eğitiriz.

---

# Nihai akış böyle olacak

```text
Yeni log gelir
↓
LLM-A: qlora_classifier_test_model
↓
Label çıkar
```

## Eğer `benign` ise:

```text
Label: benign
Explanation: üretilmez
Recommendation: No action required
```

## Eğer `malicious` ise:

```text
LLM-B: teknik açıklama üretir
LLM-C: aksiyon önerisi üretir
```

## Eğer `suspicious` ise:

Şimdilik bunu kesin saldırı gibi işlemeyeceğiz. Çünkü HDFS suspicious sınıfında tek satır log yeterli değil; balanced testte benign/suspicious ayrımının problemli olduğunu gördük. Bu durumda çıktı şöyle olacak:

```text
Label: suspicious
Status: Context required
Recommendation: Check block-level/session-level correlation
```

Yani suspicious için ileride ayrıca **context-aware HDFS anomaly module** tasarlayacağız.

---

# Kısa karar tablosu

| Modül               | Kullanılacak model            | Görev                        | Ne zaman çalışır?             |
| ------------------- | ----------------------------- | ---------------------------- | ----------------------------- |
| LLM-A               | `qlora_classifier_test_model` | Sınıflandırma                | Her logda                     |
| LLM-B               | `qlora_test_model`            | Açıklama                     | Sadece malicious/riskli logda |
| LLM-C               | `qlora_test_model`            | Öneri                        | Sadece malicious/riskli logda |
| HDFS Context Module | Henüz yok                     | Suspicious/anomaly doğrulama | Sonraki aşama                 |

---

# Şimdi yapacağımız teknik adım

Şimdi bir **pipeline script** yazacağız:

```text
analyze_log_pipeline.py
```

Bu script:

```text
1. Classifier adapter’ı yükleyecek.
2. Logu sınıflandıracak.
3. Eğer benign ise duracak.
4. Eğer malicious ise analysis adapter’a geçip açıklama ve öneri üretecek.
5. Sonucu CSV’ye kaydedecek.
```

En doğru devam bu. Çünkü artık model denemelerinden sistem mimarisine geçiyoruz.
