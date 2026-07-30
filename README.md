# Sağlık Dashboard'u — Challenge 8

KONSALT Staj Programı 2026 · Orta seviye  
Stack: Python 3 · Streamlit · requests

## Bu repo ne yapacak?

Birden fazla servisi periyodik kontrol eden mini NOC (health-check) dashboard'u.

## İzlenecek hedefler

1. Challenge 6 API — `http://127.0.0.1:8000/health`
2. Open-Meteo — hava durumu API
3. RestCountries — `https://restcountries.com/v3.1/alpha/tr`
4. Kasıtlı bozuk hedef — `http://localhost:9999/yok`

## Kurulum

```bash
pip install -r requirements.txt
```

## İlerleme

- [x] Görev 1: `check()` health check fonksiyonu
- [ ] Görev 2: Streamlit durum kartları
- [ ] Görev 3: Tarihçe + çizgi grafik
- [ ] Görev 4: Otomatik yenileme + alarm
- [ ] Bonus: hedefler.json, uptime, YAVAS yakalama
