"""Health check birim testleri — mock ile ağ çağrısı olmadan."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

import requests

from health_check import (
    HATALI,
    SAGLIKLI,
    ULASILAMIYOR,
    YAVAS,
    ardisik_ulasilamiyor_mu,
    check,
    uptime_yuzdesi,
)


class FakeResponse:
    def __init__(self, status_code: int, elapsed_s: float):
        self.status_code = status_code
        self.elapsed = MagicMock()
        self.elapsed.total_seconds.return_value = elapsed_s


class TestCheck(unittest.TestCase):
    @patch("health_check.requests.get")
    def test_saglikli_2xx_hizli(self, mock_get: MagicMock) -> None:
        mock_get.return_value = FakeResponse(200, 0.12)
        sonuc = check("http://ornek.test/health")
        self.assertEqual(sonuc["durum"], SAGLIKLI)
        self.assertEqual(sonuc["kod"], 200)
        self.assertAlmostEqual(sonuc["sure_ms"], 120.0, places=1)

    @patch("health_check.requests.get")
    def test_yavas_2xx_bir_saniye_ustu(self, mock_get: MagicMock) -> None:
        mock_get.return_value = FakeResponse(200, 1.45)
        sonuc = check("http://ornek.test/health")
        self.assertEqual(sonuc["durum"], YAVAS)
        self.assertGreaterEqual(sonuc["sure_ms"], 1000)

    @patch("health_check.requests.get")
    def test_hatali_4xx(self, mock_get: MagicMock) -> None:
        mock_get.return_value = FakeResponse(404, 0.08)
        sonuc = check("http://ornek.test/yok")
        self.assertEqual(sonuc["durum"], HATALI)
        self.assertEqual(sonuc["kod"], 404)

    @patch("health_check.requests.get")
    def test_hatali_5xx(self, mock_get: MagicMock) -> None:
        mock_get.return_value = FakeResponse(503, 0.05)
        sonuc = check("http://ornek.test/health")
        self.assertEqual(sonuc["durum"], HATALI)
        self.assertEqual(sonuc["kod"], 503)

    @patch("health_check.requests.get")
    def test_saglikli_esik_alti(self, mock_get: MagicMock) -> None:
        mock_get.return_value = FakeResponse(200, 0.999)
        self.assertEqual(check("http://ornek.test/")["durum"], SAGLIKLI)

    @patch("health_check.requests.get")
    def test_yavas_tam_bir_saniye(self, mock_get: MagicMock) -> None:
        mock_get.return_value = FakeResponse(200, 1.0)
        self.assertEqual(check("http://ornek.test/")["durum"], YAVAS)

    @patch("health_check.requests.get")
    def test_zorunlu_alanlar(self, mock_get: MagicMock) -> None:
        mock_get.return_value = FakeResponse(200, 0.05)
        sonuc = check("http://ornek.test/health")
        self.assertTrue({"durum", "sure_ms", "kod"}.issubset(sonuc.keys()))

    @patch("health_check.requests.get", side_effect=requests.ConnectionError("refused"))
    def test_ulasilamiyor_baglanti_hatasi(self, _mock_get: MagicMock) -> None:
        sonuc = check("http://localhost:9999/yok")
        self.assertEqual(sonuc["durum"], ULASILAMIYOR)
        self.assertIsNone(sonuc["kod"])
        self.assertIsNone(sonuc["sure_ms"])

    @patch("health_check.requests.get", side_effect=requests.Timeout("timed out"))
    def test_ulasilamiyor_timeout(self, _mock_get: MagicMock) -> None:
        sonuc = check("http://yavaş.test/", timeout=1)
        self.assertEqual(sonuc["durum"], ULASILAMIYOR)
        self.assertEqual(sonuc["hata"], "Timeout")


class TestUptimeVeAlarm(unittest.TestCase):
    def test_uptime_yuzdesi(self) -> None:
        kayitlar = [{"durum": SAGLIKLI}] * 80 + [{"durum": ULASILAMIYOR}] * 20
        self.assertEqual(uptime_yuzdesi(kayitlar, 100), 80.0)

    def test_ardisik_alarm(self) -> None:
        hist = [
            {"durum": SAGLIKLI},
            {"durum": ULASILAMIYOR},
            {"durum": ULASILAMIYOR},
            {"durum": ULASILAMIYOR},
        ]
        self.assertTrue(ardisik_ulasilamiyor_mu(hist, 3))
        self.assertFalse(ardisik_ulasilamiyor_mu(hist[:3], 3))


if __name__ == "__main__":
    unittest.main()
