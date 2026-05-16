# Veri Seti Hazırlama ve LLM Fine-Tuning Altyapısı Raporu

## 1. Giriş

Bu çalışma kapsamında, Büyük Dil Modelleri (Large Language Models - LLM) tabanlı akıllı bir siber güvenlik log analiz sistemi geliştirmek amacıyla gerçekçi ve etiketli bir veri işleme altyapısı hazırlanmıştır. Projenin temel amacı; sistem loglarını ve saldırı loglarını analiz ederek bunları otomatik şekilde sınıflandırabilen, açıklayabilen ve öneri üretebilen bir yapay zekâ sistemi oluşturmaktır.

Geliştirilen sistemin hedefleri şunlardır:

* Gelen log kayıtlarını analiz etmek,
* Logları:

  * benign (normal),
  * suspicious (şüpheli),
  * malicious (zararlı)

  olarak sınıflandırmak,
* Teknik açıklama üretmek,
* Olası tehdit davranışlarını yorumlamak,
* Güvenlik önerileri sunmak.

Bu amaç doğrultusunda gerçek dünyadan alınmış log veri setleri toplanmış, işlenmiş, etiketlenmiş ve LLM fine-tuning sürecine uygun hale getirilmiştir.

---

# 2. Sistem Ortamı ve Donanım Analizi

Çalışma Windows işletim sistemi üzerinde yerel geliştirme ortamında gerçekleştirilmiştir.

## 2.1 Donanım Özellikleri

| Bileşen        | Özellik                    |
| -------------- | -------------------------- |
| İşlemci        | Intel i7-13650HX           |
| Ekran Kartı    | NVIDIA RTX 4060 Laptop GPU |
| VRAM           | 8 GB                       |
| RAM            | 16 GB                      |
| Depolama       | NVMe SSD                   |
| Boş Disk Alanı | Yaklaşık 260 GB            |

---

## 2.2 Donanım Uygunluk Analizi

Yapılan analiz sonucunda:

* Tam ölçekli LLM eğitiminin mevcut VRAM kapasitesi nedeniyle uygun olmadığı,
* Ancak QLoRA tabanlı fine-tuning işlemlerinin gerçekleştirilebileceği,
* Veri ön işleme ve veri seti hazırlama süreçlerinin sistem tarafından rahatlıkla yürütülebileceği belirlenmiştir.

Sistemdeki temel darboğazın GPU değil RAM kapasitesi olduğu tespit edilmiştir. Bu nedenle veri işleme süreçlerinde chunk-based processing yaklaşımı tercih edilmiştir.

---

# 3. Veri Seti Seçim Süreci

Gerçekçi bir siber güvenlik veri seti oluşturabilmek amacıyla iki farklı veri kaynağı seçilmiştir:

1. HDFS sistem logları
2. Cowrie honeypot saldırı logları

Bu yapı sayesinde hem normal sistem davranışı hem de gerçek saldırı davranışları aynı veri kümesinde temsil edilmiştir.

---

# 3.1 HDFS Veri Seti

HDFS veri seti, dağıtık dosya sistemi davranışlarını temsil etmek amacıyla kullanılmıştır.

## Veri Seti Özellikleri

| Özellik        | Açıklama                          |
| -------------- | --------------------------------- |
| Veri Seti      | HDFS_v1                           |
| Amaç           | Normal + anomalili sistem logları |
| Tür            | Distributed File System Logs      |
| Etiket Kaynağı | anomaly_label.csv                 |

---

## Kullanılan Dosyalar

Aşağıdaki dosyalar kullanılmıştır:

```text
HDFS.log
anomaly_label.csv
```

---

## Kullanım Amacı

HDFS veri seti aşağıdaki etiketleri üretmek amacıyla kullanılmıştır:

```text
benign
suspicious
```

`anomaly_label.csv` dosyası, belirli blokların anomalili olup olmadığını belirleyen ground-truth etiketlerini içermektedir.

---

# 3.2 Cowrie Honeypot Veri Seti

Cowrie honeypot veri seti, gerçek saldırgan davranışlarını temsil etmek amacıyla kullanılmıştır.

## Veri Seti Özellikleri

| Özellik   | Açıklama                 |
| --------- | ------------------------ |
| Veri Seti | Cowrie Honeypot Logs     |
| Kaynak    | Kaggle                   |
| Tür       | SSH Honeypot Attack Logs |

---

## Kullanılan Dosyalar

Aşağıdaki günlük log dosyaları kullanılmıştır:

```text
cowrie.json.2022-11-14
...
cowrie.json.2022-11-27
```

Toplamda yaklaşık 14 günlük saldırı verisi işlenmiştir.

---

## Veri Setinin İçeriği

Cowrie veri seti içerisinde aşağıdaki saldırı davranışları gözlemlenmiştir:

* SSH brute-force saldırıları,
* Başarısız giriş denemeleri,
* Başarılı yetkisiz girişler,
* Zararlı komut çalıştırmaları,
* Dosya indirme girişimleri,
* Persistence davranışları,
* SSH tünelleme girişimleri.

Örnek event türleri:

```text
cowrie.login.failed
cowrie.login.success
cowrie.command.input
cowrie.session.file_download
```

---

# 4. Veri Ön İşleme Süreci

## 4.1 HDFS Ön İşleme

HDFS log dosyası içerisinden ilk 100.000 satır alınmıştır.

İşlem sırasında:

* `blk_...` formatındaki block ID’ler regex ile çıkarılmış,
* anomaly_label.csv ile eşleştirme yapılmış,
* etiket dönüşümü gerçekleştirilmiştir.

Etiket dönüşümü:

| Orijinal Etiket | Yeni Etiket |
| --------------- | ----------- |
| Normal          | benign      |
| Anomaly         | suspicious  |

---

## HDFS İşleme Sonucu

| Label      | Kayıt Sayısı |
| ---------- | ------------ |
| benign     | 96,951       |
| suspicious | 3,049        |

Toplam:

```text
100,000 log
```

işlenmiştir.

---

# 4.2 Cowrie Ön İşleme

Cowrie JSON log dosyaları satır satır okunmuştur.

İşlem sırasında:

* JSON parsing uygulanmış,
* eventid,
* timestamp,
* source,
* message

alanları çıkarılmıştır.

Tüm Cowrie kayıtları:

```text
malicious
```

olarak etiketlenmiştir.

---

## Cowrie İşleme Sonucu

Toplam:

```text
100,000 log
```

işlenmiştir.

---

## Event Dağılımı

En sık görülen event türleri:

| Event                  | Sayı   |
| ---------------------- | ------ |
| cowrie.command.input   | 20,336 |
| cowrie.session.params  | 18,938 |
| cowrie.log.closed      | 18,672 |
| cowrie.session.connect | 8,597  |
| cowrie.login.failed    | 5,175  |

Bu dağılım veri setinin yüksek davranış çeşitliliğine sahip olduğunu göstermektedir.

---

# 5. Birleşik Veri Seti Oluşturulması

HDFS ve Cowrie veri setleri birleştirilerek tek bir eğitim veri seti oluşturulmuştur.

Oluşturulan dosya:

```text
training_dataset.csv
```

---

## Veri Seti Dağılımı

| Label      | Kayıt Sayısı |
| ---------- | ------------ |
| malicious  | 100,000      |
| benign     | 96,951       |
| suspicious | 3,049        |

Toplam:

```text
200,000 kayıt
```

oluşturulmuştur.

---

# 6. LLM Instruction Dataset Oluşturulması

Veri seti daha sonra LLM fine-tuning işlemleri için instruction-tuning formatına dönüştürülmüştür.

Oluşturulan dosya:

```text
llm_instruction_dataset_advanced.jsonl
```

---

## Veri Formatı

Her örnek aşağıdaki yapıda hazırlanmıştır:

```json
{
  "instruction": "...",
  "input": "...",
  "output": "..."
}
```

---

## Output Yapısı

LLM çıktısı üç bölümden oluşacak şekilde tasarlanmıştır:

1. Label
2. Technical Explanation
3. Recommendation

Örnek:

```text
Label: malicious

Explanation:
Failed SSH authentication attempts indicate a possible brute-force attack.

Recommendation:
Block the source IP and enable authentication rate limiting.
```

---

# 7. Açıklama ve Recommendation Üretimi

Başlangıçta açıklamalar genel template yapısındaydı. Daha sonra event-aware açıklama sistemi geliştirilmiştir.

Örneğin:

| Event                        | Açıklama Türü                 |
| ---------------------------- | ----------------------------- |
| cowrie.login.failed          | Brute-force explanation       |
| cowrie.command.input         | Post-exploitation explanation |
| cowrie.session.file_download | Malware download explanation  |

Bu sayede veri seti yalnızca sınıflandırma değil:

* teknik reasoning,
* güvenlik analizi,
* olay yorumlama

yetkinlikleri de kazandırabilecek hale getirilmiştir.

---

# 8. Train / Validation / Test Ayrımı

LLM fine-tuning süreci için veri seti üç parçaya ayrılmıştır.

| Veri Kümesi | Kayıt Sayısı |
| ----------- | ------------ |
| Train       | 160,000      |
| Validation  | 20,000       |
| Test        | 20,000       |

Oluşturulan dosyalar:

```text
train.jsonl
validation.jsonl
test.jsonl
```

---

# 9. Mevcut Durum

Bu aşama sonunda:

* Gerçek log verileri işlenmiş,
* Etiketlenmiş veri seti oluşturulmuş,
* LLM instruction dataset hazırlanmış,
* Fine-tuning altyapısı tamamlanmıştır.

Sistem artık:

* local LLM kurulumu,
* inference testleri,
* QLoRA fine-tuning,
* evaluation,
* gerçek zamanlı log analizi

aşamalarına geçmeye hazır durumdadır.

---

# 10. Sonuç

Bu çalışma kapsamında gerçek sistem logları ve gerçek saldırı logları kullanılarak LLM tabanlı bir siber güvenlik analiz sistemi için kapsamlı bir veri hazırlama altyapısı geliştirilmiştir.

Oluşturulan veri seti:

* gerçekçi,
* çok sınıflı,
* açıklanabilir,
* instruction-tuning uyumlu

bir yapıdadır.

Bu yapı sayesinde sistemin gelecekte:

* SOC yardımcı sistemi,
* otomatik log yorumlayıcı,
* siber güvenlik copilot sistemi,
* anomali analiz platformu

olarak geliştirilebilmesi mümkün hale gelmiştir.
