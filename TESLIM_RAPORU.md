# Teslim Raporu — Challenge 8 Sağlık Dashboard'u

**Hazırlayan:** Beyza Yılmaz  
**Program:** KONSALT Staj Programı 2026  
**Challenge:** 8 — Sağlık Dashboard'u (Seviye: Orta)  
**Tarih:** 29 Temmuz 2026  
**İlgili ön koşullar:** Challenge 3 (API Keşfi), Challenge 6 (Mini Envanter API)

---

## 1. Yönetici özeti

Bu teslimde, birden fazla dış ve yerel servisin sağlığını tek ekrandan izleyen Streamlit tabanlı bir **mini NOC (Network Operations Center) paneli** geliştirilmiştir. Panel; health check sonuçlarını durum kartlarıyla gösterir, yanıt sürelerini kalıcı tarihçeye yazar, çizgi grafiklerle görselleştirir ve ardışık erişim kayıplarında operasyonel **alarm** üretir.

| Başlık | Sonuç |
|--------|--------|
| Zorunlu görevler (1–4) | Tamamlandı |
| Resmi bonuslar (3 madde) | Tamamlandı |
| Ek kalite çalışmaları | Birim testleri + yönetici dokümantasyonu |
| Challenge 6 entegrasyonu | `/health` canlı izleniyor; isteğe bağlı latency enjeksiyonu eklendi |

---

## 2. İş ihtiyacı ve çözüm yaklaşımı

Operasyon ekipleri üretimde servislere tek tek bakmaz; **tek bakışta availability + latency** sinyali bekler. Challenge senaryosu bu ihtiyacı dört hedef üzerinden simüle eder:

1. Yerel Challenge 6 Envanter API (`/health`)
2. Harici Open-Meteo forecast API
3. Harici RestCountries ülke API
4. Kasıtlı bozuk hedef (`localhost:9999`) — negatif test / alarm senaryosu

Çözüm katmanları:

| Katman | Sorumluluk |
|--------|------------|
| `health_check.check()` | Probe (prob) çalıştırma, durum sınıflandırma |
| `hedefler.json` | Hedef envanteri (configuration management) |
| `tarihce.csv` | Time-series kalıcılık (append-only log) |
| `dashboard.py` | Sunum, metrik, grafik, auto-refresh, alarm UI |

---

## 3. Teknik tasarım

### 3.1 Durum modeli (health semantics)

| Durum | Kural | Operasyonel anlam |
|-------|--------|-------------------|
| `SAGLIKLI` | HTTP 2xx ∧ latency &lt; 1.000 ms | SLA içinde |
| `YAVAS` | HTTP 2xx ∧ latency ≥ 1.000 ms | Degraded (ayakta, yavaş) |
| `HATALI` | HTTP 4xx/5xx | Servis yanıt veriyor ancak hatalı |
| `ULASILAMIYOR` | `RequestException` (timeout, connection refused vb.) | Probe başarısız; status kodu yok |

**Tasarım kararı:** "Yanıt var" ≠ "sağlıklı". Latency ayrı durum olarak modellendi; böylece performans bozulması kesinti ile karışmaz. Ayrıntılı gerekçe `SAGLIK_KURALLARI.md` içindedir.

### 3.2 Ölçüm yöntemi

- Süre ölçümü: `response.elapsed.total_seconds() * 1000`
- Timeout: varsayılan 3 saniye
- Bağlantı hataları try/except ile yakalanır (status kodu üretilmez)

### 3.3 Kalıcılık ve Streamlit çalışma modeli

Streamlit her etkileşimde scripti baştan çalıştırır. Bu nedenle session değişkenine güvenilmez; her probe sonucu `tarihce.csv` dosyasına yazılır. Grafik ve alarm hesabı dosyadaki kayıtlardan türetilir — yeniden başlatmalarda veri kaybı olmaz.

### 3.4 Alarm politikası

Aynı hedef için tarihçedeki **son 3 kayıt** `ULASILAMIYOR` ise kart üstünde **⚠ ALARM** gösterilir. Tek seferlik timeout'ların alarm üretmesi engellenerek false-positive oranı düşürülür (basit anti-flapping).

### 3.5 Otomatik yenileme

Sidebar'dan açılıp kapatılabilen 30 saniyelik döngü: `time.sleep(30)` + `st.rerun()`. Manuel "Şimdi Yenile" butonu on-demand probe için mevcuttur.

---

## 4. Bonus çalışmalar

| Bonus | Uygulama | Kanıt |
|-------|----------|--------|
| Configuration management | Hedefler `hedefler.json` dosyasından okunur | Yeni hedef eklemek için kod değişmez |
| Uptime yüzdesi | Son 100 kontrolde `SAGLIKLI` oranı | Kart ve sidebar metrikleri |
| Kasıtlı yavaşlık | Challenge 6'da `HEALTH_DELAY_SECONDS` env | `HEALTH_DELAY_SECONDS=2` → dashboard `YAVAS` |

Challenge 6 `main.py` içine opsiyonel gecikme eklendi; varsayılan davranış değişmez (`0`). Bu, latency enjeksiyonunun kontrollü bir **chaos / fault-injection** denemesi olarak kullanılmasına imkân verir.

---

## 5. Doğrulama ve kalite güvencesi

### 5.1 Manuel kontrol noktaları

| Kontrol | Beklenen sonuç | Durum |
|---------|----------------|--------|
| 4 hedef probe | 3 dış/yerel hedef sınıflanır; bozuk hedef `ULASILAMIYOR` | Geçti |
| Kart UI | Renkli durum, süre, saat, `st.metric` | Geçti |
| Tarihçe + grafik | 10+ kontrol sonrası çizgi grafik | Geçti / birikir |
| Alarm | API kapatılınca 3 yenileme → ALARM; açılınca söner | Geçti (senaryo ile) |

### 5.2 Otomatik testler

`tests/test_health_check.py` mock tabanlı senaryolar:

- 2xx hızlı → `SAGLIKLI`
- 2xx yavaş → `YAVAS`
- 5xx → `HATALI`
- `ConnectionError` / `Timeout` → `ULASILAMIYOR`
- Uptime hesabı ve ardışık alarm mantığı

```bash
python -m unittest discover -s tests -v
```

---

## 6. Çalıştırma (kısa)

```bash
# Terminal 1 — Challenge 6
cd konsalt-challenge-06-mini-envanter-api-main
python -m uvicorn main:app --port 8000

# Terminal 2 — Dashboard
cd konsalt-challenge-08-saglik-dashboardu
pip install -r requirements.txt
streamlit run dashboard.py
```

Yavaşlık demosu:

```powershell
$env:HEALTH_DELAY_SECONDS="2"
python -m uvicorn main:app --port 8000
```

---

## 7. Teslim içeriği kontrol listesi

- [x] `dashboard.py` — Streamlit uygulaması
- [x] `README.md` — kurulum ve kullanım
- [x] Ekran görüntüsü klasörü (`screenshots/`) — normal + alarmlı an
- [x] Sağlık kuralları tanımı (`SAGLIK_KURALLARI.md`)
- [x] Bonus: `hedefler.json`
- [x] Bonus: uptime yüzdesi
- [x] Bonus: Challenge 6 kasıtlı yavaşlık desteği
- [x] Ek: birim testleri ve bu teslim raporu

---

## 8. Kazanımlar ve sonraki adımlar

**Kazanılan beceriler:** health check semantiği, latency SLA eşiği, append-only metrik loglama, Streamlit ile operasyonel UI, configuration-driven hedef yönetimi, basit alarm politikası.

**İleride iyileştirilebilecekler (Challenge 10 Observability yönünde):**

- Prometheus metrik export / Grafana paneli
- Alert webhook (Slack / e-posta)
- Hedef bazlı farklı SLA eşikleri
- SQLite time-series saklama

---

## 9. Sonuç

Challenge 8 kapsamındaki zorunlu görevler ve resmi bonuslar eksiksiz tamamlanmıştır. Teslim, yalnızca "sayfa açılıyor" seviyesinde değil; **ölçülebilir durum modeli**, **kalıcı tarihçe**, **alarm politikası** ve **yapılandırılabilir hedef listesi** ile staj sürecindeki observability temeline katkı verecek şekilde hazırlanmıştır.
