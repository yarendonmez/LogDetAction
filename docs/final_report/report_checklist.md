# LogDetAction v2.0 — Rapor Kontrol Listesi

Bu dosya, final raporun tamamlanması için doldurulması veya eklenmesi gereken öğeleri listeler.
Her öğeyi tamamladıktan sonra `[ ]` işaretini `[x]` ile değiştir.

---

## 1. Kapak ve Kimlik Bilgileri

- Üniversite adı ve logosu eklenecek
- Fakülte / bölüm adı eklenecek
- Danışman adı ve unvanı eklenecek
- Resmi üniversite kapak formatı uygulanacak (`Bölüm 1` başına)

---

## 2. Ekran Görüntüleri (Şekiller)

Tüm ekran görüntüleri `docs/final_report/assets/` klasörüne kaydedilmeli ve raporun ilgili `[EKLENECEK]` satırı güncellenmeli.


| #       | Dosya Adı                      | Bölüm   | İçerik                                                                      |
| ------- | ------------------------------ | ------- | --------------------------------------------------------------------------- |
| Şekil 2 | `fig2_analyze_screen.png`      | Bölüm 9 | Analyze sekmesi — FileUploadZone veya ManualInputPanel, ModeSelector seçili |
| Şekil 3 | `fig3_progress_panel.png`      | Bölüm 9 | ProgressPanel — ilerleme çubuğu ve kısmi sonuçlar                           |
| Şekil 4 | `fig4_result_table.png`        | Bölüm 9 | ResultTable — etiket renkleri, filtre çubukları görünür                     |
| Şekil 5 | `fig5_log_detail_modal.png`    | Bölüm 9 | LogDetailModal — açıklama, öneri, zamanlama, AnalystActionPanel             |
| Şekil 6 | `fig6_analytics_dashboard.png` | Bölüm 9 | AnalyticsDashboard — KPI kartları, donut grafik, bar grafik                 |
| Şekil 7 | `fig7_live_monitor.png`        | Bölüm 9 | LiveMonitorPanel — durum kartları, canlı olay tablosu                       |
| Şekil 8 | `fig8_history_panel.png`       | Bölüm 9 | HistoryPanel — zaman filtresi, analiz listesi                               |


- fig2_analyze_screen.png
- fig3_progress_panel.png
- fig4_result_table.png
- fig5_log_detail_modal.png
- fig6_analytics_dashboard.png
- fig7_live_monitor.png
- fig8_history_panel.png

> Ek olarak eklenebilecek şekiller:
>
> - Şekil 1 için güncel mimari diyagram (PNG veya SVG)
> - Pipeline akış diyagramı (LLM-A → LLM-B / LLM-C)
> - Confusion matrix görselleştirmesi (Tablo 13 ve 15 için)

---

## 3. Birinci Dönem Raporu PDF'inden Aktarılacak Bilgiler

Kaynak: `BM495_PROJE_DÖNEMSONURAPORU_Y.DONMEZ_20252026_BAHAR.pdf`

- Tablo 1'deki eksik F1 ve ek metrik değerleri aktarılacak (Mistral-7B 50/100/500 test sonuçları)
- Qwen 2.5-3B ve Phi-2 için F1 değerleri aktarılacak (varsa)
- İlk dönem raporundaki kaynaklar listesi `Bölüm 14`'e aktarılacak
- İlk dönem raporundaki mimarı diyagramlar varsa Şekil 1 olarak kullanılabilir

---

## 4. Kaynaklar (Bölüm 14)

- LoRA / QLoRA makale tam atıfları eklenecek (Hu et al., 2022; Dettmers et al., 2023)
- Mistral-7B resmi referansı eklenecek
- HDFS log dataset kaynağı eklenecek (LogHub veya orijinal makale)
- Cowrie proje URL ve erişim tarihi eklenecek
- FastAPI, React, SQLAlchemy, Recharts, Zustand, react-i18next resmi dökümantasyon referansları eklenecek
- `transformers`, `peft`, `bitsandbytes` kütüphane referansları eklenecek
- Birinci dönem raporunda kullanılan diğer kaynaklar aktarılacak

---

## 5. Deneysel Sonuçlar

- Bölüm 8.8 (Canlı İzleme Demo Gözlemleri) — live monitor + log_generator.py ile yapılan test sonuçları eklenecek

---

## 6. İsteğe Bağlı Ekler

- Loss eğrisi grafiği — eğitim sürecindeki loss değişimini gösteren grafik (varsa loglardan oluşturulabilir)
- Eğitim süresi karşılaştırması tablosu (1000 örneklik smoke test vs balanced 3000 örneklik eğitim)
- Backend `requirements.txt` içeriği Ek'e eklenebilir

---

## 7. Biçim ve Biçimlendirme

- Tüm tablo ve şekil numaraları doğru sırayla devam ediyor mu kontrol edilecek
- `[EKLENECEK]` placeholder sayısı azaltılarak son haline getirilecek
- Resmi üniversite formatı (sayfa kenar boşlukları, yazı tipi, kapak) uygulanacak
- İçindekiler tablosundaki bağlantılar PDF'te çalışıyor mu kontrol edilecek

---

## Placeholder Özeti

Raporda toplam `[EKLENECEK]` işaretli yer tutucular:


| Tür                             | Adet |
| ------------------------------- | ---- |
| Ekran görüntüsü (şekil)         | 7    |
| Birinci dönem PDF'inden aktarım | 3+   |
| Kaynak atıfı                    | 8+   |
| Demo test sonucu                | 1    |
| Kapak formatı                   | 1    |


