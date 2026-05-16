# LogDetAction v2.0

## Log Analysis Pipeline — Analysis Mode

`analyze_log_pipeline.py`, malicious loglar için iki analiz modu destekler:

| Mod | CLI değeri | Ön yüz adı | Davranış |
|-----|------------|------------|----------|
| **Fast Mode** | `combined` (varsayılan) | Fast Mode | Explanation + Recommendation tek model çağrısında üretilir. Daha hızlı. |
| **Detailed Mode** | `separate` | Detailed Mode | Explanation ve Recommendation ayrı çağrılarla üretilir. Daha modüler; ileride ayrı LLM-B / LLM-C modellerine hazır. |

Varsayılan mod `combined`dır. Separate modda malicious loglarda toplam süre 12–21 saniyeye çıkabildiği için production / sınırlı GPU ortamında combined tercih edilir.

### Combined modda süre alanları

- Tek çağrının süresi `explanation_time_sec` alanına yazılır.
- `recommendation_time_sec` = `0.0` olur.
- CSV’de bu, combined generation süresinin explanation alanında tutulduğu anlamına gelir.

### Çalıştırma

Sanal ortamı etkinleştirdikten sonra:

#### Fast Mode / Combined (varsayılan)

```powershell
$env:PYTHONUTF8=1
python -X utf8 .\v2.0\analyze_log_pipeline.py
```

Açıkça seçmek için:

```powershell
$env:PYTHONUTF8=1
python -X utf8 .\v2.0\analyze_log_pipeline.py --mode combined
```

#### Detailed Mode / Separate

```powershell
$env:PYTHONUTF8=1
python -X utf8 .\v2.0\analyze_log_pipeline.py --mode separate
```

#### Kendi log dosyanla — combined

```powershell
$env:PYTHONUTF8=1
python -X utf8 .\v2.0\analyze_log_pipeline.py "C:\developer\LogDetAction\v2.0\sample_logs.txt" --mode combined
```

#### Kendi log dosyanla — separate

```powershell
$env:PYTHONUTF8=1
python -X utf8 .\v2.0\analyze_log_pipeline.py "C:\developer\LogDetAction\v2.0\sample_logs.txt" --mode separate
```

### CSV çıktısı

Sonuçlar `pipeline_results.csv` dosyasına yazılır. Her satırda `analysis_mode` alanı (`combined` veya `separate`) bulunur.

### Frontend / API entegrasyonu

Dropdown:

```text
Analysis Mode:
- Fast Mode
- Detailed Mode
```

Backend isteği:

```json
{
  "analysis_mode": "combined"
}
```

veya:

```json
{
  "analysis_mode": "separate"
}
```

CLI’daki `--mode combined|separate` parametresi, ileride FastAPI endpoint’inde aynı isimle alınacak şekilde tasarlanmıştır. Mimari modüler kalır; donanım güçlendiğinde ayrı LLM-B / LLM-C adapter’larına geçiş mümkündür.
