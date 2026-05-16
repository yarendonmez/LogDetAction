Aşağıdaki bölüm, **son rapordan sonra yaptığımız QLoRA fine-tuning hazırlığı ve test eğitimi** kısmını rapora ekleyebileceğin akademik formatta hazırlanmıştır.

---

# QLoRA Fine-Tuning Hazırlığı ve Test Eğitimi

## 1. Amaç

Önceki aşamada sistem üzerinde lokal LLM inference işlemleri gerçekleştirilmiş ve Mistral-7B-Instruct-v0.2 modelinin fine-tuning yapılmadan önceki performansı ölçülmüştü. Bu aşamada amaç, hazırlanan instruction dataset kullanılarak modelin yerel donanım üzerinde QLoRA yöntemiyle eğitilebilir olup olmadığını test etmektir.

Bu test eğitimi ile aşağıdaki sorulara cevap aranmıştır:

* Yerel GPU üzerinde LLM fine-tuning başlatılabiliyor mu?
* RTX 4060 Laptop GPU, 7B parametreli bir model için QLoRA eğitimini destekliyor mu?
* Dataset, tokenizer ve model pipeline’ı birlikte sorunsuz çalışıyor mu?
* LoRA adapter katmanları başarıyla eğitilebiliyor mu?
* Eğitim sırasında loss değeri düşüyor mu?
* Checkpoint sistemi çalışıyor mu?
* Eğitim çıktısı daha sonra kullanılmak üzere kaydedilebiliyor mu?

Bu nedenle bu aşama, tam ölçekli eğitimden önce bir **smoke test / feasibility test** olarak değerlendirilmiştir.

---

## 2. Eğitim Ortamının Hazırlanması

Fine-tuning işlemleri için Python sanal ortamı içinde gerekli kütüphaneler kurulmuştur. Kullanılan temel kütüphaneler şunlardır:

```text
torch
transformers
datasets
peft
bitsandbytes
tqdm
```

GPU desteğinin çalışıp çalışmadığını doğrulamak amacıyla PyTorch CUDA testi yapılmıştır. Test sonucunda CUDA’nın aktif olduğu ve sistemde NVIDIA GeForce RTX 4060 Laptop GPU’nun kullanılabildiği doğrulanmıştır.

Eğitim çıktısında da CUDA’nın aktif olduğu ve GPU’nun doğru şekilde tanındığı görülmüştür:

```text
CUDA aktif mi? True
GPU: NVIDIA GeForce RTX 4060 Laptop GPU
```

Bu sonuç, eğitim sürecinin CPU yerine GPU üzerinde gerçekleştirilebildiğini göstermektedir. 

---

## 3. Kullanılan Model

Bu aşamada kullanılan temel model:

```text
mistralai/Mistral-7B-Instruct-v0.2
```

Model yaklaşık 7 milyar parametreye sahiptir. Mevcut donanımda tam model eğitimi mümkün olmadığı için model 4-bit quantization ile yüklenmiş ve QLoRA yaklaşımı uygulanmıştır.

Modelin 4-bit olarak yüklenmesi sayesinde VRAM kullanımı azaltılmış ve RTX 4060 Laptop GPU üzerinde test eğitimi mümkün hale getirilmiştir.

---

## 4. QLoRA Yaklaşımı

Bu çalışmada modelin tamamı eğitilmemiştir. Bunun yerine LoRA adapter katmanları eğitilmiştir. Eğitim çıktısında görülen parametre dağılımı şu şekildedir:

```text
trainable params: 6,815,744
all params: 7,248,547,840
trainable%: 0.0940
```

Bu sonuç, modelin toplam 7.2 milyar parametresinden yalnızca yaklaşık 6.8 milyon parametresinin eğitildiğini göstermektedir. Başka bir ifadeyle, toplam model parametrelerinin yalnızca yaklaşık %0.094’ü eğitilmiştir. 

Bu yaklaşımın avantajları şunlardır:

* VRAM ihtiyacı ciddi şekilde azalır.
* Eğitim süresi kısalır.
* Checkpoint dosyaları daha küçük olur.
* Mevcut donanımda 7B model üzerinde deney yapmak mümkün hale gelir.
* Base model korunur, yalnızca adapter katmanları güncellenir.

Bu nedenle QLoRA, mevcut donanım koşulları için uygun bir fine-tuning yöntemi olarak seçilmiştir.

---

## 5. Eğitim Veri Seti

Bu test eğitiminde tam eğitim veri seti yerine küçük bir alt küme kullanılmıştır.

```text
Kullanılan örnek sayısı: 1000
```

Bu tercih bilinçli olarak yapılmıştır. Amaç tam performans elde etmek değil, eğitim pipeline’ının stabil şekilde çalışıp çalışmadığını test etmektir.

Kullanılan veri seti daha önce hazırlanan instruction formatındaki veri setinden alınmıştır. Her örnek şu yapıya sahiptir:

```text
Instruction
Input log
Expected response
```

Modelin öğrenmesi beklenen çıktı formatı ise:

```text
Label
Explanation
Recommendation
```

şeklindedir.

---

## 6. Eğitim Süreci

Eğitim başlatıldığında şu aşamalar başarıyla tamamlanmıştır:

1. Dataset yüklenmiştir.
2. 1000 örnek başarıyla okunmuştur.
3. Tokenizer yüklenmiştir.
4. Dataset tokenize edilmiştir.
5. Model ağırlıkları yüklenmiştir.
6. Model QLoRA için hazırlanmıştır.
7. LoRA adapter katmanları modele eklenmiştir.
8. Eğitim döngüsü başlatılmıştır.

Eğitim çıktısına göre 1000 örneklik veri seti başarıyla tokenize edilmiştir:

```text
Dataset örnek sayısı: 1000
Map: 100% ... 1000/1000
```

Model ağırlıkları da başarıyla yüklenmiştir:

```text
Loading weights: 100%
```

Ardından eğitim süreci başlamış ve 1000/1000 adım tamamlanmıştır. 

---

## 7. Loss Değerleri ve Eğitim Davranışı

Eğitim sırasında loss değerlerinin düzenli olarak düştüğü gözlemlenmiştir.

Başlangıçta:

```text
Optimizer Step: 10 | Avg Loss: 2.0490
```

Daha sonraki adımlarda:

```text
Optimizer Step: 50 | Avg Loss: 0.2428
```

Eğitimin sonlarına doğru:

```text
Optimizer Step: 250 | Avg Loss: 0.1352
```

olarak ölçülmüştür. 

Bu sonuç, modelin 1000 örneklik küçük veri seti üzerinde eğitim sinyalini alabildiğini ve adapter parametrelerinin güncellendiğini göstermektedir. Loss değerindeki hızlı düşüş, pipeline’ın çalıştığını doğrulamak açısından olumlu bir bulgudur.

Ancak burada dikkat edilmesi gereken nokta, bu sonucun yalnızca küçük ölçekli test eğitimi için geçerli olduğudur. 1000 örnek üzerinde loss’un hızlı düşmesi, modelin genel test setinde yüksek doğruluk vereceği anlamına gelmez. Bu nedenle sonraki aşamada ayrı bir evaluation yapılması gerekmektedir.

---

## 8. Checkpoint Mekanizması

Eğitim sırasında checkpoint kaydetme mekanizması da test edilmiştir. Eğitim çıktısına göre aşağıdaki checkpointler oluşturulmuştur:

```text
checkpoint-50
checkpoint-150
checkpoint-200
checkpoint-250
```

Örnek checkpoint kaydı:

```text
Checkpoint kaydedildi:
C:\developer\LogDetAction\v2.0\qlora_test_checkpoints\checkpoint-250
```

Bu, eğitim sırasında bir hata oluşması durumunda en son checkpoint’e kadar olan ilerlemenin korunabileceğini göstermektedir. 

Checkpoint mekanizması özellikle uzun süreli fine-tuning işlemleri için kritiktir. Çünkü GPU belleği, Windows sürücü problemleri, elektrik kesintisi veya kod hataları nedeniyle eğitim yarıda kesilebilir. Bu durumda checkpoint bulunması, eğitimin tamamen boşa gitmesini engeller.

---

## 9. Eğitim Süresi

1000 örneklik test eğitimi toplamda yaklaşık:

```text
28 dakika 14 saniye
```

sürmüştür.

Eğitim çıktısında son ilerleme satırı şu şekildedir:

```text
Training: 100% ... 1000/1000 [28:14]
```

Bu sonuç, mevcut donanımda 1000 örneklik QLoRA test eğitiminin yaklaşık yarım saat sürdüğünü göstermektedir. 

Bu ölçüm, daha büyük eğitim denemeleri için zaman tahmini yapmada kullanılabilir. Ancak süre doğrusal olarak artmayabilir; veri uzunluğu, token sayısı, checkpoint sıklığı ve GPU bellek kullanımı toplam eğitim süresini etkileyebilir.

---

## 10. Modelin Kaydedilmesi

Eğitim tamamlandıktan sonra model adapter çıktısı başarıyla kaydedilmiştir.

Kaydedilen model yolu:

```text
C:\developer\LogDetAction\v2.0\qlora_test_model
```

Eğitim çıktısında bu durum şu şekilde görülmektedir:

```text
Training tamamlandı. Model kaydediliyor...
Model kaydedildi:
C:\developer\LogDetAction\v2.0\qlora_test_model
```

Bu çıktı, LoRA adapter modelinin daha sonra yeniden yüklenip test edilebileceğini göstermektedir. 

---

## 11. Bu Aşamada Elde Edilen Bulgular

Bu test eğitimi sonucunda aşağıdaki bulgular elde edilmiştir:

| Bulgu                      | Değerlendirme                   |
| -------------------------- | ------------------------------- |
| CUDA aktif çalıştı         | GPU eğitim için kullanılabildi  |
| RTX 4060 modeli tanındı    | Donanım uyumluluğu doğrulandı   |
| 7B model 4-bit yüklendi    | QLoRA için uygun ortam sağlandı |
| 1000 örnek tokenize edildi | Dataset pipeline çalıştı        |
| LoRA adapter eklendi       | Fine-tuning mimarisi çalıştı    |
| Loss değeri düştü          | Eğitim sinyali alındı           |
| Checkpoint kaydedildi      | Hata toleransı sağlandı         |
| Final adapter kaydedildi   | Test modeli elde edildi         |

Bu bulgular, tam ölçekli QLoRA fine-tuning işlemine geçmeden önce sistemin temel olarak hazır olduğunu göstermektedir.

---

## 12. Karşılaşılan Problemler ve Çözümler

Bu aşamada bazı teknik problemlerle karşılaşılmıştır.

### 12.1 Windows Encoding Problemi

`TRL/SFTTrainer` kullanımında Windows Türkçe karakter kodlaması nedeniyle `cp1254` kaynaklı hata alınmıştır. Bu problemi çözmek için Python UTF-8 modunda çalıştırılmıştır:

```powershell
$env:PYTHONUTF8=1
python -X utf8 .\v2.0\train_qlora_test.py
```

Bu ayar, Windows ortamında Python’un UTF-8 encoding ile çalışmasını sağlamıştır.

### 12.2 SFTTrainer Uyumsuzluğu

Kullanılan `trl` sürümünde `SFTTrainer` parametreleri beklenenden farklı davranmıştır. Ayrıca mixed precision ve gradient scaling aşamasında BF16 kaynaklı hata alınmıştır.

Bu nedenle `SFTTrainer` yerine manuel bir QLoRA training loop geliştirilmiştir. Bu değişiklikle:

* model doğrudan yüklenmiş,
* LoRA adapter manuel olarak eklenmiş,
* optimizer manuel tanımlanmış,
* forward/backward işlemleri manuel yapılmış,
* checkpoint sistemi elle yönetilmiştir.

Bu yaklaşım, `Accelerate`/`SFTTrainer` kaynaklı uyumsuzluğu bypass ederek eğitimin başarıyla tamamlanmasını sağlamıştır.

### 12.3 Uyarılar

Eğitim sırasında bazı uyarılar görülmüştür:

```text
triton not found
```

Bu uyarı FLOP hesaplaması ile ilgilidir ve eğitimin çalışmasını engellememiştir.

Ayrıca PyTorch checkpoint kullanımıyla ilgili `use_reentrant` uyarısı görülmüştür. Bu da eğitim sürecini durdurmamış, yalnızca ilerideki PyTorch sürümleri için parametre verilmesi gerektiğini belirtmiştir.

---

## 13. Genel Değerlendirme

Bu aşamada yapılan çalışma, projenin LLM fine-tuning kısmının teknik olarak uygulanabilir olduğunu göstermiştir. Yerel donanım üzerinde Mistral-7B-Instruct-v0.2 modeli 4-bit quantization ile yüklenmiş, QLoRA adapter katmanları eklenmiş ve 1000 örnek üzerinde başarılı şekilde eğitilmiştir.

Bu test eğitimi sonucunda:

* GPU uyumluluğu doğrulanmıştır.
* QLoRA pipeline çalıştırılmıştır.
* Loss değerlerinin düştüğü gözlemlenmiştir.
* Checkpoint sistemi doğrulanmıştır.
* Fine-tune edilmiş test adapter modeli oluşturulmuştur.

Bu nedenle proje, bir sonraki aşamada fine-tune edilmiş adapter’ın test edilmesi ve base model ile karşılaştırılması için hazır duruma gelmiştir.

---

## 14. Sonraki Aşama

Bir sonraki aşamada yapılacak işlem, kaydedilen QLoRA adapter modelini yükleyerek test seti üzerinde değerlendirme yapmaktır.

Planlanan karşılaştırma:

| Model                         | 3-Class Accuracy | Attack Detection Accuracy |
| ----------------------------- | ---------------: | ------------------------: |
| Base Mistral-7B-Instruct-v0.2 |              %60 |                       %70 |
| QLoRA Test Adapter            |        Ölçülecek |                 Ölçülecek |

Bu karşılaştırma sayesinde küçük ölçekli QLoRA fine-tuning işleminin model performansına etkisi ölçülecektir.

Eğer test adapter olumlu sonuç verirse, sonraki aşamada eğitim veri sayısı kademeli olarak artırılacaktır:

```text
1000 örnek → 5000 örnek → 10000 örnek → daha büyük eğitim
```

Bu kademeli yaklaşım, hem donanım sınırlarını kontrollü şekilde test etmeyi hem de zaman kaybını azaltmayı sağlayacaktır.
