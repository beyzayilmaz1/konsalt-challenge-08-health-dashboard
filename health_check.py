"""Health check çekirdeği — Challenge 8 Görev 1."""

from __future__ import annotations

import requests

# 2xx ve süre bu eşiğin altındaysa SAGLIKLI, üstündeyse YAVAS
YAVAS_ESIGI_MS = 1000


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
