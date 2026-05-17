Evet, bunu rahat savunabiliriz; hatta **projenin en dürüst ve akademik güçlü bulgularından biri** bu. Ekranda canlı izleme 31 logda `19 malicious / 0 suspicious / 12 benign` göstermiş. Bu “hata” gibi görünmesin; bizim test sonuçlarımız zaten modelin suspicious sınıfında zayıf, malicious-benign ayrımında güçlü olduğunu kanıtlamıştı.

## Neden suspicious az/hiç çıkmıyor?

Elimizdeki en önemli veri şu: gelişmiş instruction dataset’te sınıf dağılımı zaten çok dengesizdi:

| Label      | Örnek Sayısı |
| ---------- | -----------: |
| malicious  |      100.000 |
| benign     |       96.951 |
| suspicious |        3.049 |

Yani suspicious, veri setinin çok küçük bir kısmıydı. İlk classifier-only test eğitiminde bu daha da belirgindi: 1000 örnek içinde yalnızca **12 suspicious** vardı. Bu yüzden ana classifier modelin suspicious sınıfını güçlü öğrenmemesi beklenen bir durum. 

Daha net kanıt balanced testte ortaya çıktı. Her sınıftan 100 örnek seçtiğimiz testte ana classifier model:

```text id="skdqy4"
benign: 100/100 doğru
malicious: 99/100 doğru
suspicious: 0/100 doğru
```

yani suspicious örneklerin tamamını benign olarak tahmin etti. Buna rağmen attack detection accuracy **299/300 = %99.67** çıktı. Bu bize şunu gösterdi: model saldırı tespitinde çok güçlü, ama HDFS suspicious/anomaly sınıfını tek satırdan ayırmakta zayıf. 

## Balanced modeli neden kullanmadık?

Çünkü suspicious yakalayan modeli denedik. Balanced training sonrası suspicious recall **0.86** oldu; yani suspicious sınıfını yakalamaya başladı. Ama bedeli çok ağırdı: benign recall **0.18**’e düştü. Confusion matrix’te 100 benign logun 82’si suspicious tahmin edildi. Bu da gerçek sistemde çok fazla yanlış alarm demek. 

Bu yüzden ana model olarak balanced classifier’ı seçmedik. Çünkü projede güvenli ve kullanılabilir bir SOC prototipi için şu daha mantıklıydı:

```text id="zgjggw"
Malicious saldırıları yüksek doğrulukla yakala.
Benign loglarda gereksiz alarm üretme.
Suspicious sınıfını bağlam gerektiren özel durum olarak ele al.
```

## Akademik savunma cümlesi

Rapora veya jüriye şöyle diyebilirsin:

> Bu sistemde suspicious sınıfının az veya hiç üretilmesi beklenen bir davranıştır. Çünkü mevcut ana classifier modeli, deneysel sonuçlara göre malicious-benign ayrımında yüksek başarı göstermiş; ancak HDFS tabanlı suspicious/anomaly kayıtlarını tek satır düzeyinde ayırmakta zorlanmıştır. Balanced training ile suspicious recall artırılabilmiş, ancak bu durumda benign loglarda yüksek false positive oluşmuştur. Bu nedenle ana prototipte attack detection başarısı ve düşük yanlış alarm oranı önceliklendirilmiş; suspicious sınıfı ise context-required / block-level correlation gerektiren bir kategori olarak korunmuştur.

## UI’da nasıl göstermeliyiz?

Bence `Şüpheli` kartını kaldırma. Ama ismini/tooltip’ini daha doğru yap:

```text id="5zro45"
Şüpheli / Bağlam Gerekli
```

Tooltip:

```text id="l6t7ol"
Bu sınıf, özellikle HDFS/anomali loglarında tek satırdan güvenilir belirlenemeyebilir. Şüpheli olayların daha sağlıklı tespiti için block-level, session-level veya zaman serisi bağlamı gereklidir.
```

Canlı izleme ekranında `Şüpheli 0` görünmesi kötü değil. Hatta savunması şu:

```text id="4d746k"
Canlı modül şu anda tek satır bazlı analiz yapıyor. Suspicious sınıfı ise çoğunlukla bağlam gerektirdiği için bu modda az görülmesi beklenmektedir.
```

## Sonuç

Yani net cevap: **Evet, model pek suspicious bulmuyor; bunu saklamayacağız. Bunu deneysel bulgu ve sistem sınırlılığı olarak savunacağız.** Ana iddiamız suspicious yakalamak değil; domain-specific QLoRA ile saldırı tespitini güçlendirmek, benign loglarda gereksiz analiz üretmemek, riskli loglara açıklama/öneri üretmek ve güvenli human-in-the-loop pipeline kurmak.
