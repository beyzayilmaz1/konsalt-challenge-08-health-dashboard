# Teslim Raporu — Challenge 8 Sağlık Dashboard'u

**Program:** KONSALT Staj Programı 2026  
**Challenge:** 8 — Sağlık Dashboard'u (Mini NOC)  
**Seviye:** Orta  
**Stack:** Python 3 · Streamlit · requests · pandas

---

## 1. Özet

Operasyon ekiplerinin dağınık servislere tek tek bakmak yerine tek ekrandan izlediği NOC yaklaşımının küçük bir uygulaması üretildi. Dashboard dört hedefi periyodik kontrol eder; durumu renkli kartlarla gösterir; yanıt süresi tarihçesini çizer; ardışık erişim kayıplarında alarm üretir.

| Madde | Açıklama |
| --- | --- |
| Problem | Servis sağlığını tek bakışta görmek |
| Çözüm | Streamlit tabanlı canlı health-check dashboard |
| Durum modeli | SAGLIKLI / YAVAS / HATALI / ULASILAMIYOR |
| Kalıcılık | Her kontrol `tarihce.csv` dosyasına append edilir |
| Alarm | Üst üste 3 ULASILAMIYOR → kartta ⚠ ALARM |
| Yapılandırma | Hedefler `hedefler.json` üzerinden yönetilir |

---

## 2. Kapsam

### Zorunlu görevler

| Görev | İçerik | Durum |
| --- | --- | --- |
| 1 | `check(url)` — dört durum modeli | Tamamlandı |
| 2 | Streamlit kartlar + Yenile butonu | Tamamlandı |
| 3 | `tarihce.csv` + `st.line_chart` | Tamamlandı |
| 4 | 30 sn otomatik yenileme + 3× alarm | Tamamlandı |

### Bonus / ek

| Madde | Durum |
| --- | --- |
| `hedefler.json` configuration management | Tamamlandı |
| Son 100 kontrol uptime % | Tamamlandı |
| Challenge 6 gecikmesi ile YAVAS yakalama | Dokümante edildi |
| Birim testleri + GitHub Actions CI | Tamamlandı |
| `SAGLIK_KURALLARI.md` | Tamamlandı |

---

## 3. Mimari kararlar

1. **Domain / UI ayrımı:** Ölçüm ve kurallar `health_check.py` içinde; sunum `dashboard.py` içinde. Streamlit her rerun'da scripti baştan çalıştırdığı için tarihçe dosyada tutulur.
2. **1 sn eşiği + YAVAS ayrı durum:** Çalışıyor ile sağlıklı ayrılır; latency bozulması kesintiden farklı müdahale ister. Ayrıntı: `SAGLIK_KURALLARI.md`.
3. **Alarm eşiği 3:** Tek seferlik timeout flapping'ini azaltmak için ardışık üç başarısızlık gerekir.
4. **JSON ile hedef listesi:** Yeni servis eklemek kod değişikliği gerektirmez.

```
hedefler.json ──► dashboard.py ──► health_check.check()
                      │                    │
                      ▼                    ▼
               tarihce.csv ◄──── requests.get(url)
                      │
                      ▼
         uptime / alarm / grafikler
```

---

## 4. Doğrulama

- Dört hedef için doğru durum dönüşü (bozuk hedef → ULASILAMIYOR)
- Dashboard kartları ve renkler
- Biriken tarihçe ile çizgi grafikler
- Challenge 6 kapalıyken 3 yenileme sonrası ALARM; açılınca sönmesi
- `python -m unittest discover -s tests -v` — mock tabanlı birim testleri
- GitHub Actions CI (`.github/workflows/ci.yml`)

---

## 5. Bilinen sınırlar

- Her Streamlit rerun'ında yeni probe çalışır ve CSV'ye kayıt eklenir.
- `tarihce.csv` için retention / rotation yoktur.
- Retry yoktur; tek probe sonucu kullanılır.
- Harici API'ler (Open-Meteo, RestCountries) ağ koşullarına bağlıdır.

---

## 6. Sonraki iyileştirmeler

- SQLite / zaman serisi saklama
- Slack / e-posta alarm bildirimi
- Docker ile tek komut çalıştırma
- Retry + exponential backoff

---

## 7. Teslim dosyaları

| Dosya | Rol |
| --- | --- |
| `dashboard.py` | Streamlit UI |
| `health_check.py` | check / tarihçe / alarm / uptime |
| `hedefler.json` | Hedef listesi |
| `SAGLIK_KURALLARI.md` | Eşik gerekçesi |
| `TESLIM_RAPORU.md` | Bu rapor |
| `README.md` | Çalıştırma kılavuzu |
| `tests/` | Birim testleri |
| `.github/workflows/ci.yml` | CI |
| `screenshots/` | Ekran görüntüleri (opsiyonel eklenir) |
| `requirements.txt` | Bağımlılıklar |
