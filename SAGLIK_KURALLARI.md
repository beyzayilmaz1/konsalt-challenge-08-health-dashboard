# Sağlık Kuralları

Bu dashboard'da bir servisin "çalışıyor" olması ile "sağlıklı" olması aynı şey değildir.
Health check dört duruma ayrılır; eşiğin gerekçesi aşağıdadır.

## Durum modeli

| Durum | Koşul | Anlamı |
| --- | --- | --- |
| **SAGLIKLI** | HTTP 2xx ve yanıt &lt; 1000 ms | Servis erişilebilir ve kabul edilebilir hızda |
| **YAVAS** | HTTP 2xx ve yanıt ≥ 1000 ms | Servis ayakta ama latency bozulmuş |
| **HATALI** | HTTP 4xx / 5xx | Bağlantı var; uygulama hata dönüyor |
| **ULASILAMIYOR** | Timeout / bağlantı hatası | Status kodu yok; servise ulaşılamıyor |

## Neden 1 saniye eşiği?

- Operasyon ekranlarında "kullanıcı fark eder" gecikme çoğu zaman saniye mertebesindedir.
- Challenge kapsamı için yuvarlak, ölçülebilir ve kolay test edilebilir bir sınır gerekir.
- Challenge 6 API'ye kasıtlı `time.sleep(2)` eklendiğinde dashboard'un **YAVAS** yakalayıp yakalamadığı net görülür.
- Daha sıkı (ör. 300 ms) veya daha gevşek (ör. 3 sn) eşikler de mümkün; kritik olan eşik seçiminin bilinçli olmasıdır.

Bu projede eşik `health_check.py` içinde `YAVAS_ESIGI_MS = 1000` olarak tutulur.

## Neden YAVAS ayrı bir durum?

- **Çalışıyor ≠ sağlıklı.** 2xx dönmek, kullanıcı deneyiminin iyi olduğu anlamına gelmez.
- Kesinti (`ULASILAMIYOR` / `HATALI`) ile performans bozulması farklı müdahale ister:
  - Kesintide: servisi ayağa kaldırma, ağ / DNS kontrolü
  - Yavaşlıkta: kaynak, DB, bağımlı API veya overload incelemesi
- Tek "kötü" kova kullanılırsa latency alarmı ya hiç çıkmaz ya da her yavaş cevapta yanlış alarm üretir.
- NOC bakışında sarı kart, kırmızı/siyahtan önce erken uyarı verir.

## Alarm eşiği (3 × ULASILAMIYOR)

Tek seferlik timeout'ların (geçici ağ takılması) hemen panik yaratmaması için ardışık 3 başarısızlık gerekir.
Bu basit bir anti-flapping kuralıdır.

## YAVAS'ı nasıl doğrularım?

Challenge 6 API terminalinde kasıtlı gecikme:

```powershell
$env:HEALTH_DELAY_SECONDS="2"
python -m uvicorn main:app --port 8000
```

Dashboard'da Mini Envanter kartı **🟡 YAVAS** olmalı (yanıt ~2000 ms).
