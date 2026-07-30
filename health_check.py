"""Health check çekirdeği — Challenge 8."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

import requests

# 2xx ve süre bu eşiğin altındaysa SAGLIKLI, üstündeyse YAVAS
YAVAS_ESIGI_MS = 1000
TARIHCE_DOSYASI = Path("tarihce.csv")
TARIHCE_ALANLAR = ["zaman", "hedef", "durum", "sure_ms", "kod"]


def check(url: str, timeout: float = 3) -> dict:
    """Tek bir URL'yi kontrol eder.

    Dönüş:
        {"durum": "SAGLIKLI"|"YAVAS"|"HATALI"|"ULASILAMIYOR",
         "sure_ms": float | None,
         "kod": int | None}
    """
    try:
        response = requests.get(url, timeout=timeout)
        sure_ms = response.elapsed.total_seconds() * 1000
        kod = response.status_code

        if 200 <= kod < 300:
            durum = "SAGLIKLI" if sure_ms < YAVAS_ESIGI_MS else "YAVAS"
        else:
            durum = "HATALI"

        return {"durum": durum, "sure_ms": round(sure_ms, 1), "kod": kod}

    except requests.RequestException:
        # Bağlantı kurulamadı / timeout → status kodu yok
        return {"durum": "ULASILAMIYOR", "sure_ms": None, "kod": None}


def kaydet(hedef: str, sonuc: dict, dosya: Path = TARIHCE_DOSYASI) -> None:
    """Kontrol sonucunu tarihce.csv dosyasına append eder."""
    yeni = not dosya.exists()
    with dosya.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=TARIHCE_ALANLAR)
        if yeni:
            writer.writeheader()
        writer.writerow(
            {
                "zaman": datetime.now().isoformat(timespec="seconds"),
                "hedef": hedef,
                "durum": sonuc["durum"],
                "sure_ms": sonuc["sure_ms"] if sonuc["sure_ms"] is not None else "",
                "kod": sonuc["kod"] if sonuc["kod"] is not None else "",
            }
        )


def tarihce_oku(dosya: Path = TARIHCE_DOSYASI) -> list[dict]:
    """tarihce.csv içeriğini satır listesi olarak döndürür."""
    if not dosya.exists():
        return []
    with dosya.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def alarm_var(hedef: str, esik: int = 3, dosya: Path = TARIHCE_DOSYASI) -> bool:
    """Hedefin son N kaydı hep ULASILAMIYOR ise True."""
    kayitlar = [k for k in tarihce_oku(dosya) if k.get("hedef") == hedef]
    if len(kayitlar) < esik:
        return False
    sonlar = kayitlar[-esik:]
    return all(k.get("durum") == "ULASILAMIYOR" for k in sonlar)


def uptime_yuzde(hedef: str, pencere: int = 100, dosya: Path = TARIHCE_DOSYASI) -> float | None:
    """Son N kontrolde SAGLIKLI oranını yüzde olarak döndürür.

    Kayıt yoksa None.
    """
    kayitlar = [k for k in tarihce_oku(dosya) if k.get("hedef") == hedef]
    if not kayitlar:
        return None
    sonlar = kayitlar[-pencere:]
    saglikli = sum(1 for k in sonlar if k.get("durum") == "SAGLIKLI")
    return round(100.0 * saglikli / len(sonlar), 1)
