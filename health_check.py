"""
Health check çekirdeği — dashboard ve birim testleri tarafından paylaşılır.

Durum modeli (SLA eşiği: 1 saniye):
  SAGLIKLI      → HTTP 2xx ve yanıt < 1000 ms
  YAVAS         → HTTP 2xx ve yanıt >= 1000 ms
  HATALI        → HTTP 4xx / 5xx
  ULASILAMIYOR  → bağlantı hatası, DNS, timeout vb.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Optional

import requests

SAGLIKLI = "SAGLIKLI"
YAVAS = "YAVAS"
HATALI = "HATALI"
ULASILAMIYOR = "ULASILAMIYOR"

DURUM_IKON = {
    SAGLIKLI: "🟢",
    YAVAS: "🟡",
    HATALI: "🔴",
    ULASILAMIYOR: "⚫",
}

# Operasyonel eşik: 1 sn altında "sağlıklı", üstünde "yavaş ama ayakta"
YAVASLIK_ESIGI_MS = 1000.0


def check(url: str, timeout: float = 3.0) -> dict[str, Any]:
    """
    Tek bir hedefe health check yapar.

    Returns:
        {"durum": str, "sure_ms": float | None, "kod": int | None, "hata": str | None}
    """
    try:
        response = requests.get(url, timeout=timeout)
        sure_ms = response.elapsed.total_seconds() * 1000
        kod = response.status_code

        if 200 <= kod < 300:
            durum = SAGLIKLI if sure_ms < YAVASLIK_ESIGI_MS else YAVAS
        else:
            durum = HATALI

        return {
            "durum": durum,
            "sure_ms": round(sure_ms, 2),
            "kod": kod,
            "hata": None,
        }
    except requests.RequestException as exc:
        # Bağlantı kurulamadığında status kodu yoktur.
        return {
            "durum": ULASILAMIYOR,
            "sure_ms": None,
            "kod": None,
            "hata": type(exc).__name__,
        }


def uptime_yuzdesi(kayitlar: list[dict[str, Any]], pencere: int = 100) -> Optional[float]:
    """Son N kontrolün yüzde kaçının SAGLIKLI olduğunu hesaplar."""
    if not kayitlar:
        return None
    son = kayitlar[-pencere:]
    saglikli = sum(1 for k in son if k.get("durum") == SAGLIKLI)
    return round(100.0 * saglikli / len(son), 1)


def ardisik_ulasilamiyor_mu(kayitlar: list[dict[str, Any]], esik: int = 3) -> bool:
    """Hedefin son `esik` kaydı hep ULASILAMIYOR mu?"""
    if len(kayitlar) < esik:
        return False
    return all(k.get("durum") == ULASILAMIYOR for k in kayitlar[-esik:])


def ardisik_ulasilamiyor_sayisi(kayitlar: list[dict[str, Any]]) -> int:
    """Sondan başlayarak ardışık ULASILAMIYOR kayıt sayısı."""
    sayac = 0
    for kayit in reversed(kayitlar):
        if kayit.get("durum") == ULASILAMIYOR:
            sayac += 1
        else:
            break
    return sayac


def sure_ms_oku(deger: Any) -> float | None:
    if deger in ("", None):
        return None
    try:
        return float(deger)
    except (TypeError, ValueError):
        return None


def sure_formatla(saniye: int) -> str:
    if saniye < 60:
        return f"{saniye}s"
    dakika, sn = divmod(saniye, 60)
    if dakika < 60:
        return f"{dakika}m {sn}s"
    saat, dakika = divmod(dakika, 60)
    return f"{saat}h {dakika}m"


def alarm_suresi_saniye(
    kayitlar: list[dict[str, Any]],
    esik: int = 3,
    yenileme_saniye: int = 30,
) -> int | None:
    """Aktif alarm varsa ardışık erişim kaybının süresini saniye cinsinden döner."""
    if not ardisik_ulasilamiyor_mu(kayitlar, esik):
        return None

    ardisik = []
    for kayit in reversed(kayitlar):
        if kayit.get("durum") == ULASILAMIYOR:
            ardisik.append(kayit)
        else:
            break

    if len(ardisik) < 2:
        return max(0, (len(ardisik) - 1) * yenileme_saniye)

    try:
        def _parse(zaman: str) -> datetime:
            metin = str(zaman)
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
                try:
                    return datetime.strptime(metin, fmt)
                except ValueError:
                    continue
            return datetime.fromisoformat(metin)

        son = _parse(str(ardisik[0]["zaman"]))
        ilk = _parse(str(ardisik[-1]["zaman"]))
        return max(0, int((son - ilk).total_seconds()))
    except (ValueError, KeyError, TypeError):
        return max(0, (len(ardisik) - 1) * yenileme_saniye)


def alarm_detay_metni(
    kayitlar: list[dict[str, Any]],
    esik: int = 3,
    yenileme_saniye: int = 30,
) -> str | None:
    if not ardisik_ulasilamiyor_mu(kayitlar, esik):
        return None
    adet = ardisik_ulasilamiyor_sayisi(kayitlar)
    sure = alarm_suresi_saniye(kayitlar, esik, yenileme_saniye)
    sure_txt = "—" if sure is None else sure_formatla(sure)
    return f"Son {adet} kontrol ulaşılamadı · Süre: {sure_txt}"


def son_kayit_zamani(
    kayitlar: list[dict[str, Any]],
    kosul: Callable[[dict[str, Any]], bool],
) -> str | None:
    for kayit in reversed(kayitlar):
        if kosul(kayit):
            zaman = kayit.get("zaman")
            return str(zaman) if zaman else None
    return None


def son_basari_zamani(kayitlar: list[dict[str, Any]]) -> str | None:
    return son_kayit_zamani(kayitlar, lambda k: k.get("durum") == SAGLIKLI)


def son_hata_zamani(kayitlar: list[dict[str, Any]]) -> str | None:
    return son_kayit_zamani(kayitlar, lambda k: k.get("durum") != SAGLIKLI)


def operasyon_ozeti_hesapla(sonuclar: list[dict[str, Any]]) -> dict[str, Any]:
    sayilar = {SAGLIKLI: 0, YAVAS: 0, HATALI: 0, ULASILAMIYOR: 0}
    sureler: list[float] = []

    for sonuc in sonuclar:
        durum = sonuc.get("durum")
        if durum in sayilar:
            sayilar[durum] += 1
        sure = sure_ms_oku(sonuc.get("sure_ms"))
        if sure is not None:
            sureler.append(sure)

    ortalama = round(sum(sureler) / len(sureler), 1) if sureler else None
    return {
        "toplam": len(sonuclar),
        "ortalama_sure_ms": ortalama,
        "saglikli": sayilar[SAGLIKLI],
        "yavas": sayilar[YAVAS],
        "hatali": sayilar[HATALI],
        "ulasilamiyor": sayilar[ULASILAMIYOR],
    }


def incident_log_kayitlari(
    tarihce: list[dict[str, Any]],
    limit: int = 12,
    alarm_esigi: int = 3,
) -> list[dict[str, str]]:
    incidents: list[dict[str, str]] = []
    ard_isik_sayac: dict[str, int] = {}
    durum_css = {
        SAGLIKLI: "ok",
        YAVAS: "warn",
        HATALI: "bad",
        ULASILAMIYOR: "down",
    }

    for kayit in tarihce:
        hedef = str(kayit.get("hedef", "Bilinmeyen"))
        durum = str(kayit.get("durum", ""))
        if durum == ULASILAMIYOR:
            ard_isik_sayac[hedef] = ard_isik_sayac.get(hedef, 0) + 1
        else:
            ard_isik_sayac[hedef] = 0

        if durum == SAGLIKLI:
            continue

        etiket = "ALARM" if durum == ULASILAMIYOR and ard_isik_sayac[hedef] >= alarm_esigi else durum
        css = "alarm" if etiket == "ALARM" else durum_css.get(durum, "down")
        incidents.append(
            {
                "zaman": str(kayit.get("zaman", "—")),
                "hedef": hedef,
                "etiket": etiket,
                "css": css,
            }
        )

    return list(reversed(incidents[-limit:]))
