# Sağlık Dashboard'u — Challenge 8

KONSALT Staj Programı 2026 · Orta seviye  
Stack: Python 3 · Streamlit · requests

## Bu repo ne yapacak?

Birden fazla servisi periyodik kontrol eden mini NOC (health-check) dashboard'u.
Durum modeli: **SAGLIKLI / YAVAS / HATALI / ULASILAMIYOR**.

## İzlenecek hedefler

Hedefler `hedefler.json` dosyasından okunur:

1. Challenge 6 API — `http://127.0.0.1:8000/health`
2. Open-Meteo — hava durumu API
3. RestCountries — `https://restcountries.com/v3.1/alpha/tr`
4. Kasıtlı bozuk hedef — `http://localhost:9999/yok`

## Kurulum

```bash
pip install -r requirements.txt
```

## Çalıştırma

Challenge 6 API (ayrı terminal):

```bash
cd ../konsalt-challenge-06-mini-envanter-api-main
python -m uvicorn main:app --port 8000
```

Dashboard:

```bash
python -m streamlit run dashboard.py
```

Tarayıcı: http://localhost:8501

## İlerleme

- [x] Görev 1: `check()` health check fonksiyonu
- [x] Görev 2: Streamlit durum kartları
- [x] Görev 3: Tarihçe (`tarihce.csv`) + çizgi grafik
- [x] Görev 4: Otomatik yenileme (30 sn) + 3× ULASILAMIYOR alarmı
- [x] Bonus: hedefler.json (configuration management)
- [x] Bonus: uptime % (son 100 kontrol)
- [x] Bonus: YAVAS yakalama (Challenge 6 gecikmesi)
- [x] Teslim: SAGLIK_KURALLARI.md + screenshots/
- [x] Ek: Operasyon özeti + Incident Log
- [x] Ek: Birim testleri + GitHub Actions CI

> `tarihce.csv` çalışma zamanında oluşur; git'e eklenmez.
> Yeni servis eklemek için `hedefler.json` dosyasına obje eklemeniz yeterli — kod değişmez.

Sağlık kurallarının gerekçesi: [SAGLIK_KURALLARI.md](SAGLIK_KURALLARI.md)  
Yönetici teslim raporu: [TESLIM_RAPORU.md](TESLIM_RAPORU.md)

## Doğrulama

### Alarm

1. Challenge 6 API'yi durdurun.
2. Üç kez **Şimdi Yenile** (veya ~90 sn otomatik yenileme).
3. Mini Envanter kartında **⚠ ALARM** görünmeli.
4. API'yi tekrar açınca alarm sönmeli.

### Bonus: YAVAS yakalama

```powershell
$env:HEALTH_DELAY_SECONDS="2"
python -m uvicorn main:app --port 8000
```

Dashboard Mini Envanter kartında **🟡 YAVAS** görünmeli (~2000 ms).

## Teslim paketi

| Dosya | Rol |
| --- | --- |
| `dashboard.py` | Streamlit uygulaması |
| `health_check.py` | check / tarihçe / alarm / uptime |
| `hedefler.json` | İzlenecek hedefler |
| `SAGLIK_KURALLARI.md` | Neden 1 sn? Neden YAVAS ayrı? |
| `TESLIM_RAPORU.md` | Yönetici teslim raporu |
| `README.md` | Bu kılavuz |
| `screenshots/` | Normal + alarmlı ekran görüntüleri |
| `tests/` | Birim testleri |
| `.github/workflows/ci.yml` | Otomatik test (GitHub Actions) |
| `requirements.txt` | Bağımlılıklar |

## Testler

```bash
python -m unittest discover -s tests -v
```

Push / PR sonrası GitHub Actions aynı komutu çalıştırır: `.github/workflows/ci.yml`
