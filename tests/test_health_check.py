"""check() birim testleri — gerçek ağ çağrısı yok, requests mock edilir."""

from __future__ import annotations

import unittest
from datetime import timedelta
from unittest.mock import MagicMock, patch

import requests

from health_check import check


def _sahte_yanit(status_code: int, sure_sn: float) -> MagicMock:
    yanit = MagicMock()
    yanit.status_code = status_code
    yanit.elapsed = timedelta(seconds=sure_sn)
    return yanit


class CheckTestleri(unittest.TestCase):
    @patch("health_check.requests.get")
    def test_saglikli(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _sahte_yanit(200, 0.2)
        sonuc = check("http://ornek.test")
        self.assertEqual(sonuc["durum"], "SAGLIKLI")
        self.assertEqual(sonuc["kod"], 200)
        self.assertAlmostEqual(sonuc["sure_ms"], 200.0, places=0)

    @patch("health_check.requests.get")
    def test_yavas(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _sahte_yanit(200, 1.5)
        sonuc = check("http://ornek.test")
        self.assertEqual(sonuc["durum"], "YAVAS")
        self.assertEqual(sonuc["kod"], 200)

    @patch("health_check.requests.get")
    def test_hatali(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _sahte_yanit(500, 0.1)
        sonuc = check("http://ornek.test")
        self.assertEqual(sonuc["durum"], "HATALI")
        self.assertEqual(sonuc["kod"], 500)

    @patch("health_check.requests.get")
    def test_ulasilamiyor(self, mock_get: MagicMock) -> None:
        mock_get.side_effect = requests.ConnectionError("baglanti yok")
        sonuc = check("http://ornek.test")
        self.assertEqual(sonuc["durum"], "ULASILAMIYOR")
        self.assertIsNone(sonuc["kod"])
        self.assertIsNone(sonuc["sure_ms"])


if __name__ == "__main__":
    unittest.main()
