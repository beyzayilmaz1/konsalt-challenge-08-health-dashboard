# Sağlık Kuralları Tanımı

**Proje:** Challenge 8 — Sağlık Dashboard'u  
**Hazırlayan:** Beyza Yılmaz  
**Kapsam:** Health check durum modeli ve eşik gerekçeleri

---

## 1. "Çalışıyor" ile "sağlıklı" aynı şey değildir

Bir endpoint'in HTTP 200 dönmesi, servisin **ayakta** olduğunu gösterir; ancak kullanıcı deneyimi açısından **yeterince hızlı** olduğu anlamına gelmez. NOC ekranlarında bu iki kavram bilinçli olarak ayrılır:

| Kavram | Soru | Dashboard karşılığı |
|--------|------|---------------------|
| Availability (erişilebilirlik) | Servise ulaşıyor muyuz? | `ULASILAMIYOR` vs diğerleri |
| Correctness (doğruluk) | Anlamlı HTTP yanıtı mı? | `HATALI` (4xx/5xx) |
| Latency (gecikme) | Kabul edilebilir sürede mi? | `SAGLIKLI` vs `YAVAS` |

Bu ayrım olmadan yavaşlayan bir API, "yeşil" görünmeye devam eder; operasyon ekibi sorunu geç fark eder.

---

## 2. Neden 1 saniye eşiği?

Challenge kapsamında **1.000 ms** eşik olarak seçilmiştir. Gerekçeler:

1. **İnsan algısı:** Web etkileşimlerinde ~1 sn civarı, "anında" ile "bekliyorum" arasındaki tipik sınırdır (kullanıcı deneyimi literatüründe sık referans verilen bir eşik bandı).
2. **Health check bağlamı:** `/health` gibi hafif uçlar veritabanı taraması yapmamalıdır; 1 sn'nin üzerinde yanıt, bağımlılık tıkanması veya kaynak baskısı sinyali verebilir.
3. **Yanlış pozitif dengesi:** Çok düşük eşik (ör. 100 ms) ağ jitter'ı yüzünden sürekli sarı üretir; çok yüksek eşik (ör. 5 sn) gerçek bozulmayı gizler. 1 sn, staj/lab ortamı için anlaşılır ve ölçülebilir bir orta yoldur.
4. **Ölçüm kaynağı:** Süre `requests` kütüphanesinin `response.elapsed` alanından alınır; ek kronometre tutulmaz — tutarlı ve tekrarlanabilir ölçüm sağlar.

> Üretim SLA'larında eşik, servis sınıfına göre değişir (ör. senkron ödeme API'si vs. arka plan raporu). Bu projede amaç, **eşik kavramını** ve **durum ayrımını** doğru modellemektir.

---

## 3. Neden `YAVAS` ayrı bir durum?

`YAVAS`, servisin **çökmüş** olmadığını ama **performans bozulması** yaşadığını işaret eder:

| Durum | Tipik aksiyon |
|-------|----------------|
| 🟢 SAGLIKLI | İzlemeye devam |
| 🟡 YAVAS | Kapasite / bağımlılık incelemesi; trend grafiğine bak |
| 🔴 HATALI | Uygulama / gateway hata oranı; log ve status kodu analizi |
| ⚫ ULASILAMIYOR | Ağ, DNS, process down; alarm ve eskalasyon |

Tek bir "kötü" kova kullanılırsa:

- Yavaşlık ile kesinti aynı öncelikte görünür,
- Alarm yorgunluğu artar,
- Kök neden analizi zorlaşır.

`YAVAS` sayesinde dashboard, **degraded** (bozulmuş ama ayakta) senaryosunu görünür kılar. Bonus doğrulama: Challenge 6 API'sinde `HEALTH_DELAY_SECONDS=2` ile kasıtlı gecikme eklendiğinde kartın 🟡'e düşmesi bu ayrımın işe yaradığını kanıtlar.

---

## 4. `ULASILAMIYOR` ve try/except zorunluluğu

`requests.get` bağlantı kuramazsa (port kapalı, timeout, DNS) **exception** fırlatır; ortada bir HTTP status kodu yoktur. Bu yüzden `check()` fonksiyonu try/except ile sarılmıştır:

- Exception → `ULASILAMIYOR` (`kod=null`, `sure_ms=null`)
- 4xx/5xx → `HATALI` (servis cevap veriyor ama sağlıksız)
- 2xx + süre → `SAGLIKLI` veya `YAVAS`

Bu ayrım, "servis yok" ile "servis hata dönüyor" vakalarını operasyonel olarak ayırır.

---

## 5. Alarm eşiği: üst üste 3 kontrol

Tek seferlik bir timeout geçici ağ gürültüsü olabilir. **Ardışık 3** `ULASILAMIYOR` kaydı, flapping'i (titreme) azaltır ve yanlış alarm oranını düşürür. Eşik aşıldığında kart üstünde **⚠ ALARM** gösterilir; servis toparlanınca sayaç doğal olarak sıfırlanır (son 3 kayıt artık ULASILAMIYOR değildir).

---

## 6. Özet matris

| Durum | HTTP | Süre | Anlam |
|-------|------|------|--------|
| SAGLIKLI | 2xx | &lt; 1 sn | Beklenen sağlıklı davranış |
| YAVAS | 2xx | ≥ 1 sn | Ayakta ama latency SLA dışı |
| HATALI | 4xx/5xx | (ölçülür) | Uygulama / gateway hatası |
| ULASILAMIYOR | yok | yok | Erişim yok / timeout |
