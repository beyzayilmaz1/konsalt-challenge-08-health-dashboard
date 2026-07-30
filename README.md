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

## Çalıştırma

```bash
python -m streamlit run dashboard.py
```

Tarayıcı açılır: http://localhost:8501

> Challenge 6 API ayaktaysa Mini Envanter kartı 🟢 olur; kapalıysa ⚫ ULASILAMIYOR.

## İlerleme

- [x] Görev 1: `check()` health check fonksiyonu
- [x] Görev 2: Streamlit durum kartları
- [x] Görev 3: Tarihçe (`tarihce.csv`) + çizgi grafik
- [x] Görev 4: Otomatik yenileme (30 sn) + 3× ULASILAMIYOR alarmı
- [ ] Bonus: hedefler.json, uptime, YAVAS yakalama

> `tarihce.csv` çalışma zamanında oluşur; git'e eklenmez.

### Alarm testi

1. Challenge 6 API'yi durdurun.
2. Üç kez **Şimdi Yenile** (veya ~90 sn otomatik yenileme bekleyin).
3. Mini Envanter kartında **⚠ ALARM** görünmeli.
4. API'yi tekrar açınca alarm sönmeli.
