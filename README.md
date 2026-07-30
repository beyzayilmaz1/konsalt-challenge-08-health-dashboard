# Sağlık Dashboard'u — Mini NOC Ekranı

**KONSALT Staj Programı 2026 · Challenge 8**  
Seviye: Orta · Stack: Python 3 · Streamlit · requests · pandas  
Ön koşullar: Challenge 3 ve Challenge 6

Operasyon ekiplerinin sistemlere tek tek bakmak yerine tek ekrandan izlediği NOC (Network Operations Center) yaklaşımının minik bir uygulaması. Birden fazla servisi periyodik kontrol eder; durumu yeşil / sarı / kırmızı / siyah kartlarla gösterir; yanıt süresi tarihçesini çizer; ardışık erişim kayıplarında alarm üretir.

---

## Yönetici özeti

| Madde | Açıklama |
| --- | --- |
| **Problem** | Dağınık servislerin sağlığını tek bakışta görmek |
| **Çözüm** | Streamlit tabanlı canlı health-check dashboard |
| **İzlenen hedefler** | Challenge 6 API, Open-Meteo, RestCountries, kasıtlı bozuk hedef |
| **Durum modeli** | SAGLIKLI / YAVAS / HATALI / ULASILAMIYOR |
| **Kalıcılık** | Her kontrol `tarihce.csv` dosyasına append edilir |
| **Alarm** | Üst üste 3 ULASILAMIYOR → kart üstünde ⚠ ALARM |
| **Bonus** | `hedefler.json`, uptime %, YAVAS yakalama |
| **Ek özellik** | Operasyon özeti + Incident Log + Servis SLA özeti |
| **CI** | GitHub Actions ile otomatik birim testleri |

### Galip Bey ile paylaşılacak resmi teslim listesi

| Zorunlu | Dosya |
| --- | --- |
| Streamlit uygulaması | `dashboard.py` |
| Kılavuz + ekran görüntüleri | `README.md` + `screenshots/` (normal + **alarmlı** an) |
| Sağlık kuralları tanımı | `SAGLIK_KURALLARI.md` — neden 1 sn eşiği, neden YAVAS ayrı? |

> Ekran görüntülerini `screenshots/01-normal.png` ve `screenshots/02-alarm.png` olarak ekleyin.

---

## Hızlı başlangıç

### 1. Bağımlılıklar

```bash
cd konsalt-challenge-08-health-dashboard
pip install -r requirements.txt
```

### 2. Challenge 6 API'yi başlatın (ayrı terminal)

```bash
cd ../konsalt-challenge-06-mini-envanter-api-main
pip install -r requirements.txt
python -m uvicorn main:app --port 8000
```

`GET http://127.0.0.1:8000/health` → `{"status":"ok"}` dönmelidir.

### 3. Dashboard'u çalıştırın

```bash
python -m streamlit run dashboard.py
```

> Windows'ta `streamlit` komutu tanınmıyorsa `python -m streamlit run dashboard.py` kullanın.

Tarayıcı: [http://localhost:8501](http://localhost:8501)

---

## Challenge kapsamı

| Görev | İçerik | Durum |
| --- | --- | --- |
| 1 | `check(url, timeout=3)` — dört durum modeli | Tamamlandı |
| 2 | Streamlit durum kartları + `st.metric` + Yenile butonu | Tamamlandı |
| 3 | `tarihce.csv` + `st.line_chart` yanıt süresi grafikleri | Tamamlandı |
| 4 | 30 sn otomatik yenileme + 3× ULASILAMIYOR alarmı | Tamamlandı |
| Bonus | `hedefler.json` configuration management | Tamamlandı |
| Bonus | Son 100 kontrol uptime yüzdesi | Tamamlandı |
| Bonus | Challenge 6’da kasıtlı yavaşlık ile YAVAS yakalama | Destekleniyor |
| Ek | Operasyon özeti + Incident Log + Servis SLA | Tamamlandı |
| Ek | Birim testleri + GitHub Actions CI | Tamamlandı |
| Ek | `SAGLIK_KURALLARI.md` + `TESLIM_RAPORU.md` | Tamamlandı |

---

## Health check kuralları (kısa)

| Durum | Koşul | Kart |
| --- | --- | --- |
| **SAGLIKLI** | HTTP 2xx ve süre &lt; 1000 ms | 🟢 |
| **YAVAS** | HTTP 2xx ve süre ≥ 1000 ms | 🟡 |
| **HATALI** | HTTP 4xx / 5xx | 🔴 |
| **ULASILAMIYOR** | Bağlantı hatası / timeout (status kodu yok) | ⚫ |

Ayrıntılı gerekçe: [SAGLIK_KURALLARI.md](SAGLIK_KURALLARI.md).

---

## İzlenecek hedefler

Hedef listesi kodda sabit değildir; `hedefler.json` dosyasından okunur:

| Ad | URL |
| --- | --- |
| Mini Envanter API | `http://127.0.0.1:8000/health` |
| Open-Meteo | `https://api.open-meteo.com/v1/forecast?latitude=41&longitude=29&current_weather=true` |
| RestCountries | `https://restcountries.com/v3.1/alpha/tr` |
| Bozuk Hedef | `http://localhost:9999/yok` |

Yeni servis eklemek için JSON’a bir obje eklemeniz yeterlidir — `dashboard.py` değişmez.

---

## Doğrulama senaryoları

### Temel (4 kart, doğru renkler)

1. Challenge 6 API ayaktayken dashboard’u açın.
2. Beklenen: Mini Envanter + Open-Meteo + RestCountries → 🟢 (veya ağ gecikmesinde 🟡); Bozuk Hedef → ⚫ ULASILAMIYOR.
3. **Şimdi Yenile** ile anlık tekrar kontrol edin.

### Alarm (Kontrol noktası 4)

1. Challenge 6 API’yi durdurun (Ctrl+C).
2. Dashboard’un 3 otomatik yenilemesini bekleyin (~90 sn) veya üç kez **Şimdi Yenile**’ye basın.
3. Mini Envanter kartında **⚠ ALARM** görünmelidir.
4. API’yi yeniden başlatın → sonraki kontrollerde alarm söner, durum 🟢’e döner.

### Bonus: YAVAS yakalama

Challenge 6 `/health` endpoint’ine kasıtlı gecikme ekleyin (örnek):

```python
import time
# health() içinde:
time.sleep(2)
```

Dashboard Mini Envanter kartında **🟡 YAVAS** görünmelidir (yanıt ~2000 ms).

### Operasyon özeti + Incident Log + SLA

- Üst bölümde toplam servis, durum dağılımı ve ortalama yanıt süresi.
- **Servis SLA özeti:** hedef bazında uptime %, ort. süre, son durum, alarm.
- **Incident Log:** SAGLIKLI olmayan olaylar; 3× ULASILAMIYOR’da etiket `ALARM`.

### Birim testleri

```bash
python -m unittest discover -s tests -v
```

---

## Mimari

```
hedefler.json ──► dashboard.py ──► health_check.check()
                      │                    │
                      ▼                    ▼
               tarihce.csv ◄──── requests.get(url)
                      │
                      ▼
    uptime / alarm / SLA / incident / grafikler
```

- Streamlit her etkileşimde scripti **baştan** çalıştırır; bu yüzden tarihçe bellekte değil dosyada tutulur.
- Otomatik yenileme: `time.sleep(30)` + `st.rerun()` (sidebar’dan kapatılabilir).
- Alarm hesabı: ilgili hedefin `tarihce.csv` içindeki son 3 kaydına bakılır.

---

## Engineering decisions

### Neden `hedefler.json`?

- Challenge bonus kapsamına uygun **configuration management** sağlar.
- Yeni servis eklemek için kod değiştirmeye gerek kalmaz.

### Neden `tarihce.csv`?

- Streamlit her rerun’da state’i sıfırlar; kalıcılık dosyada tutulmalıdır.
- Append-only CSV, grafik / uptime / incident için ortak kaynaktır.

### Neden 1 saniye eşiği ve `YAVAS` ayrı durum?

- “Çalışıyor” ile “sağlıklı” aynı şey değildir.
- Latency bozulması kesintiden ayrı görülmelidir.
- Ayrıntı: [SAGLIK_KURALLARI.md](SAGLIK_KURALLARI.md).

### Neden alarm eşiği 3?

- Tek seferlik timeout’ların panik üretmesi engellenir (anti-flapping).

### Neden `health_check.py` / `dashboard.py` ayrımı?

- Domain mantığı ile sunum ayrılır; test edilebilir çekirdek (`check`, `alarm_var`, `uptime_yuzde`) UI’dan bağımsız kalır.

---

## Known limitations

- Her Streamlit rerun’ında yeni probe çalışır ve `tarihce.csv`’ye kayıt eklenir.
- `tarihce.csv` sınırsız büyür; retention / rotation yoktur.
- Retry mekanizması yoktur; tek probe sonucu kullanılır.
- Harici API’ler (Open-Meteo, RestCountries) ağ koşullarına bağlıdır.
- Çoklu kullanıcı senaryosunda CSV eşzamanlı yazım riski teoriktir.

---

## Future improvements

- SQLite / PostgreSQL ile zaman serisi saklama
- Slack veya e-posta alarm bildirimi
- Docker ile tek komutla çalıştırma
- Retry + exponential backoff
- Dashboard erişimi için kimlik doğrulama

---

## CI

Push veya pull request sonrası GitHub Actions birim testlerini çalıştırır:

```bash
python -m unittest discover -s tests -v
```

Workflow: [.github/workflows/ci.yml](.github/workflows/ci.yml)

---

## Ekran görüntüleri

| Dosya | Açıklama |
| --- | --- |
| `screenshots/01-normal.png` | Dört kartın sağlıklı / ulasilamiyor görünümü |
| `screenshots/02-alarm.png` | Challenge 6 kapalıyken alarmlı an |

---

## Hızlı doğrulama (5 dk)

Challenge 6 API ve dashboard çalışırken:

```bash
python -c "import json; from health_check import check; [print(h['ad'], check(h['url'])['durum']) for h in json.load(open('hedefler.json',encoding='utf-8'))]"
```

Beklenen: ilk üç hedef `SAGLIKLI` (veya `YAVAS`), `Bozuk Hedef` → `ULASILAMIYOR`.

Alarm testi: Challenge 6’yı durdurun → 3 kez **Şimdi Yenile** → Mini Envanter’de ⚠ ALARM.

---

## Teslim paketi

| Dosya | Rol |
| --- | --- |
| `dashboard.py` | Streamlit uygulaması |
| `health_check.py` | check / tarihçe / alarm / uptime / SLA / incident |
| `hedefler.json` | İzlenecek hedefler |
| `SAGLIK_KURALLARI.md` | Eşik tasarımı gerekçesi |
| `TESLIM_RAPORU.md` | Yöneticiye yönelik teknik teslim raporu |
| `README.md` | Bu proje raporu / kılavuz |
| `tests/` | Mock tabanlı birim testleri |
| `.github/workflows/ci.yml` | Push/PR’de otomatik test |
| `screenshots/` | Dashboard ekran görüntüleri |
| `requirements.txt` | Bağımlılıklar |

---

## İlgili belgeler

- [SAGLIK_KURALLARI.md](SAGLIK_KURALLARI.md) — neden 1 sn eşiği, neden YAVAS ayrı?
- [TESLIM_RAPORU.md](TESLIM_RAPORU.md) — yönetici teslim raporu
