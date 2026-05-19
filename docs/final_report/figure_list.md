# LogDetAction v2.0 — Şekil Listesi

Bu dosya, final rapordaki tüm şekillerin başlıklarını, bölüm konumlarını ve beklenen içeriklerini listeler.

---

| Şekil No | Başlık | Bölüm | Dosya Adı | Durum |
|---|---|---|---|---|
| Şekil 1 | Sistem Genel Mimarisi | 6.1 | Metin tabanlı diyagram (rapor içinde) | ✅ Raporda mevcut (ASCII diyagram) |
| Şekil 2 | Analiz Ekranı — Dosya Yükleme ve Manuel Giriş | 9 | `assets/fig2_analyze_screen.png` | ⬜ Eklenecek |
| Şekil 3 | İlerleme Paneli ve Kısmi Sonuçlar | 9 | `assets/fig3_progress_panel.png` | ⬜ Eklenecek |
| Şekil 4 | Sonuç Tablosu | 9 | `assets/fig4_result_table.png` | ⬜ Eklenecek |
| Şekil 5 | Log Detay Modalı | 9 | `assets/fig5_log_detail_modal.png` | ⬜ Eklenecek |
| Şekil 6 | Analitik Gösterge Paneli | 9 | `assets/fig6_analytics_dashboard.png` | ⬜ Eklenecek |
| Şekil 7 | Canlı İzleme Paneli | 9 | `assets/fig7_live_monitor.png` | ⬜ Eklenecek |
| Şekil 8 | Geçmiş Analiz Paneli | 9 | `assets/fig8_history_panel.png` | ⬜ Eklenecek |

---

## Opsiyonel Ek Şekiller

Raporun güçlendirilmesi için eklenebilecek isteğe bağlı şekiller:

| Şekil No | Başlık | Önerilen Konum | Dosya Adı |
|---|---|---|---|
| Şekil 9 | LLM-A / LLM-B / LLM-C Pipeline Akış Diyagramı | Bölüm 5.2 | `assets/fig9_pipeline_flow.png` |
| Şekil 10 | Confusion Matrix — İlk Classifier-Only Model | Bölüm 8.5 | `assets/fig10_cm_initial.png` |
| Şekil 11 | Confusion Matrix — Balanced-Trained Classifier | Bölüm 8.6 | `assets/fig11_cm_balanced.png` |
| Şekil 12 | QLoRA Eğitim Loss Eğrisi | Bölüm 5.1 | `assets/fig12_loss_curve.png` |
| Şekil 13 | Header — Sistem Durumu ve Dil Geçişi | Bölüm 7.2 | `assets/fig13_header.png` |

---

## Ekran Görüntüsü Alma Rehberi

1. Backend'i başlat: `python -m uvicorn backend.main:app --reload`
2. Frontend'i başlat: `cd frontend && npm run dev`
3. Tarayıcıda `http://localhost:5173` adresini aç
4. Her sekmeyi ekran görüntüsü almadan önce gerçek analiz verisiyle doldur:
   - `v2.0/data/splits/test_balanced_10.txt` dosyasını yükle
   - Analizi tamamla (model yüklüyse)
5. Tarayıcı geliştirici araçlarıyla ekran genişliğini 1440px olarak ayarla
6. Her şekli `assets/` klasörüne kaydet ve rapordaki ilgili `[EKLENECEK]` satırını güncelle

---

## Rapordaki Tablo Listesi

| Tablo No | Başlık | Bölüm |
|---|---|---|
| Tablo 1 | İlk Dönem Model Karşılaştırması | 3.2 |
| Tablo 2 | Geliştirme Ortamı Donanım Özellikleri | 4.1 |
| Tablo 3 | Gelişmiş Instruction Dataset Dağılımı | 4.3 |
| Tablo 4 | Classifier-Only Dataset Split | 4.4 |
| Tablo 5 | LLM Modül Tanımları | 5.2 |
| Tablo 6 | Analiz Modu Karşılaştırması | 5.5 |
| Tablo 7 | Güvenli Kapsam Sınırı | 6.6 |
| Tablo 8 | Backend API Endpoint Listesi | 7.1.4 |
| Tablo 9 | Base Mistral-7B Performansı | 8.1 |
| Tablo 10 | Base Mistral vs Full-Output QLoRA | 8.2 |
| Tablo 11 | Classifier-Only QLoRA Sonuçları | 8.4 |
| Tablo 12 | Balanced Evaluation — İlk Classifier-Only Model | 8.5 |
| Tablo 13 | Confusion Matrix — İlk Classifier-Only Model | 8.5 |
| Tablo 14 | Balanced-Trained Classifier Sonuçları | 8.6 |
| Tablo 15 | Confusion Matrix — Balanced-Trained Classifier | 8.6 |
| Tablo 16 | Per-Class Metrikler — Balanced-Trained Classifier | 8.6 |
| Tablo 17 | Combined vs Separate Pipeline Zamanlama | 8.7 |
