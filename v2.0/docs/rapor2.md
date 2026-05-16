# LLM Tabanlı Siber Güvenlik Log Analiz Sistemi – Inference, Evaluation ve Bulgular Raporu

# 1. Giriş

Bu aşamada proje, yalnızca veri seti hazırlama seviyesinden çıkarılarak gerçek bir Large Language Model (LLM) inference ve değerlendirme altyapısına dönüştürülmüştür. Önceki aşamalarda oluşturulan instruction-tuning veri setleri kullanılarak lokal ortamda çalışan bir dil modeli üzerinden gerçek zamanlı log analizi testleri gerçekleştirilmiştir.

Bu sürecin temel amacı:

* Generic bir LLM modelinin siber güvenlik loglarını anlayabilme seviyesini ölçmek,
* Fine-tuning öncesi başlangıç başarı seviyesini (baseline) belirlemek,
* Modelin hata yaptığı durumları analiz etmek,
* Gerçek saldırı tespiti performansını değerlendirmek,
* Inference sürelerini ölçmek,
* Domain-specific fine-tuning gerekliliğini doğrulamaktır.

Bu kapsamda LM Studio kullanılarak lokal inference ortamı kurulmuş ve Mistral-7B-Instruct modeli Python backend üzerinden çalıştırılmıştır.

---

# 2. Lokal LLM Ortamının Kurulması

## 2.1 LM Studio Kullanımı

Projede inference işlemleri için LM Studio tercih edilmiştir.

Tercih edilme nedenleri:

* GGUF formatlı modelleri kolay çalıştırabilmesi,
* GPU acceleration desteği,
* Local API server özelliği,
* Python backend sistemleri ile kolay entegrasyon sağlayabilmesi,
* RTX 4060 gibi orta segment GPU’larda stabil çalışabilmesi.

---

## 2.2 Kullanılan Model

| Özellik      | Değer                    |
| ------------ | ------------------------ |
| Model        | Mistral-7B-Instruct-v0.2 |
| Format       | GGUF                     |
| Quantization | Q4_K_M                   |

Model yaklaşık 4–5 GB boyutunda quantized şekilde çalıştırılmıştır.

---

## 2.3 GPU Kullanımı

LM Studio üzerinde GPU acceleration aktif edilmiştir.

Inference sırasında:

* Ortalama yaklaşık 45 token/sec üretim hızı elde edilmiştir.
* RTX 4060 GPU başarılı şekilde kullanılmıştır.
* CPU tabanlı inference’a kıyasla ciddi performans artışı gözlemlenmiştir.

Bu aşama, gelecekte yapılacak QLoRA fine-tuning işlemlerinin donanımsal olarak mümkün olduğunu doğrulamıştır.

---

# 3. Python – LM Studio Entegrasyonu

## 3.1 Local API Server

LM Studio local server özelliği aktif edilmiştir.

Kullanılan endpoint:

```text id="3y1wq6"
http://localhost:1234/v1/chat/completions
```

Python tarafında `requests` kütüphanesi ile modele HTTP POST istekleri gönderilmiştir.

---

## 3.2 İlk Inference Testleri

İlk testlerde modele doğrudan saldırı logları gönderilmiş ve modelden aşağıdaki formatta cevap üretmesi istenmiştir:

```text id="c8n5x4"
Label
Explanation
Recommendation
```

Örnek log:

```text id="m6r2v9"
CMD: echo "root:QoL8LLO1AmmV"|chpasswd|bash
```

Model bu logu:

```text id="q4k8u1"
malicious
```

olarak yorumlamış ve root parola değiştirme girişimini privilege abuse olarak değerlendirmiştir.

Bu sonuç modelin:

* shell command analizi,
* sistem komutlarını yorumlama,
* privilege escalation davranışlarını algılama,
* güvenlik reasoning üretme

yeteneğine sahip olduğunu göstermiştir.

---

# 4. Otomatik Evaluation Sistemi

## 4.1 Evaluation Scripti

Model performansını ölçmek amacıyla otomatik evaluation scripti geliştirilmiştir.

Script aşağıdaki işlemleri gerçekleştirmektedir:

1. Test veri setinden log okuma,
2. Logu modele gönderme,
3. Model cevabından label çıkarma,
4. Gerçek label ile karşılaştırma,
5. Accuracy hesaplama,
6. Inference süresi ölçme,
7. Sonuçları CSV dosyasına kaydetme.

---

## 4.2 Ölçülen Metrikler

İki farklı başarı metriği kullanılmıştır.

### 4.2.1 3-Class Accuracy

Üç sınıf doğrudan değerlendirilmiştir:

```text id="z8x4w1"
benign
suspicious
malicious
```

---

### 4.2.2 Attack Detection Accuracy

Bu metrikte sınıflar şu şekilde dönüştürülmüştür:

```text id="v5u7n2"
malicious → attack
benign + suspicious → non_attack
```

Bu yaklaşım gerçek saldırı tespit performansını daha doğru ölçebilmek amacıyla tercih edilmiştir.

---

# 5. Evaluation Sonuçları

İlk 10 örnek üzerinde gerçekleştirilen testlerde aşağıdaki sonuçlar elde edilmiştir.

| Metrik                    | Sonuç |
| ------------------------- | ----- |
| 3-Class Accuracy          | %60   |
| Attack Detection Accuracy | %70   |

---

# 6. Test Sonuçlarının Detaylı Analizi

## 6.1 Başarılı Sonuçlar

Model özellikle HDFS normal sistem loglarında başarılı performans göstermiştir.

Örnek:

```text id="j6r3v8"
BLOCK* NameSystem.addStoredBlock
```

ve

```text id="b4m8t1"
Receiving block
```

gibi loglar model tarafından doğru şekilde:

```text id="f8x5q2"
benign
```

olarak sınıflandırılmıştır.

Model bu logları:

* normal distributed file system activity,
* standart block transfer işlemleri,
* olağan Hadoop davranışı

olarak yorumlayabilmiştir.

Bu durum modelin:

* sistem operasyonlarını anlayabildiğini,
* HDFS yapısını temel seviyede yorumlayabildiğini,
* normal davranışı saldırıdan ayırabildiğini

göstermektedir.

---

## 6.2 Başarısız Sonuçlar

Bazı malicious loglar model tarafından benign olarak değerlendirilmiştir.

Örnek:

```text id="y2k9n4"
Remote SSH version: SSH-2.0-libssh-0.6.3
```

Model bu logu benign olarak değerlendirmiştir.

Bunun temel sebebi:

* generic modelin honeypot context bilgisine sahip olmaması,
* Cowrie event yapısını bilmemesi,
* SSH version bilgisini tek başına saldırı göstergesi olarak yorumlamamasıdır.

---

## 6.3 Reconnaissance Davranışı Problemi

Aşağıdaki log:

```text id="u8m5v3"
CMD: cat /proc/cpuinfo | grep name | wc -l
```

dataset tarafından malicious olarak etiketlenmiştir.

Model ise bunu benign olarak yorumlamıştır.

Aslında model burada tamamen anlamsız bir hata yapmamıştır.

Çünkü bu komut:

* CPU çekirdek sayısını öğrenmeye yönelik,
* reconnaissance (keşif) davranışı içerebilecek,
* ancak tek başına doğrudan saldırı kanıtı olmayan

bir komuttur.

Bu durum modelin belirli seviyede semantic reasoning yapabildiğini göstermektedir.

Ancak model:

```text id="h5n7r1"
honeypot içindeki shell command execution
```

davranışının saldırı zincirinin parçası olduğunu henüz öğrenmemiştir.

Bu problem doğrudan fine-tuning ihtiyacını göstermektedir.

---

# 7. Weak Labeling Problemi

Evaluation sırasında HDFS veri seti ile ilgili önemli bir problem tespit edilmiştir.

HDFS veri setindeki suspicious etiketleri:

```text id="k9w3v7"
satır bazlı saldırı etiketi değildir
```

Bunlar block-level anomaly etiketleridir.

Bu nedenle bazı log satırları semantik olarak normal görünmesine rağmen suspicious label taşıyabilmektedir.

Örnek:

```text id="s4x8m2"
PacketResponder terminating
```

Model bu logu benign olarak değerlendirmiştir.

Aslında bu davranış teknik olarak mantıklıdır çünkü:

* PacketResponder terminating işlemi normal HDFS davranışı olabilir,
* tek satır bazında açık saldırı göstergesi içermemektedir.

Ancak dataset içerisindeki ilgili block anomalili olduğu için suspicious etiketi verilmiştir.

Bu problem akademik olarak:

```text id="r6n2w9"
weak labeling
label granularity problem
```

olarak değerlendirilmektedir.

---

# 8. Inference Süresi Analizi

Yapılan ölçümlerde benign loglar genellikle:

```text id="n8q4v1"
3–5 saniye
```

arasında analiz edilmiştir.

Malicious loglarda ise süre:

```text id="e4u7x6"
5–15 saniye
```

seviyesine çıkmıştır.

---

## 8.1 Süre Farkının Sebebi

Malicious loglarda model:

* daha fazla reasoning yapmakta,
* daha uzun explanation üretmekte,
* daha fazla token oluşturmaktadır.

Bu durum inference süresini artırmaktadır.

Özellikle:

* shell command yorumlama,
* privilege abuse reasoning,
* SSH davranışı analizi

gibi işlemler modelin daha uzun düşünmesine neden olmaktadır.

---

# 9. Benign Log Optimizasyonu

Evaluation sürecinde önemli bir optimizasyon fikri ortaya çıkmıştır.

Benign loglarda:

```text id="z2m6r5"
uzun explanation üretmenin gereksiz olduğu
```

değerlendirilmiştir.

Önerilen yapı:

## benign

```text id="g8x4u1"
Label: benign
Recommendation: No action required.
```

## suspicious / malicious

```text id="m3v7q9"
Label
Explanation
Recommendation
```

Bu yaklaşım sayesinde:

* inference süresi azaltılabilir,
* token maliyeti düşürülebilir,
* sistem gerçek SOC davranışına yaklaştırılabilir.

Ancak generic LLM modellerinin prompt kurallarına tam uymadığı gözlemlenmiştir.

Bu problemin kalıcı çözümünün fine-tuning ile sağlanabileceği değerlendirilmiştir.

---

# 10. Sistem Mimarisinin Netleşmesi

Bu aşamada sistem mimarisi belirginleşmiştir.

Planlanan yapı:

```text id="d7k3v5"
Frontend UI
↓
Python Backend (FastAPI)
↓
LM Studio Local Server
↓
Mistral LLM
↓
Cybersecurity Analysis Engine
```

Ayrıca Cursor IDE’nin LM Studio local API’sine erişebileceği doğrulanmıştır.

Bu sayede proje geliştirme sürecinin:

* Cursor,
* Python backend,
* lokal LLM inference sistemi

üzerinden sürdürülebileceği netleşmiştir.

---

# 11. Genel Değerlendirme

Bu aşama sonunda proje:

* local LLM inference,
* automated evaluation,
* performance measurement,
* cybersecurity reasoning analysis,
* attack detection testing

yeteneklerine sahip çalışan bir prototip seviyesine ulaşmıştır.

Elde edilen bulgular şunları göstermektedir:

* Generic LLM modelleri temel seviyede güvenlik reasoning yapabilmektedir.
* Ancak honeypot-specific context bilgisine sahip değildir.
* Fine-tuning olmadan yüksek doğruluk sağlamak zordur.
* Domain-specific training kritik öneme sahiptir.
* HDFS veri setinde weak labeling problemi bulunmaktadır.
* Prompt engineering tek başına yeterli değildir.
* Gerçek performans artışı için QLoRA fine-tuning gereklidir.

Bu sonuçlar, bir sonraki aşamada gerçekleştirilecek QLoRA fine-tuning sürecinin projenin en kritik aşaması olacağını göstermektedir.



