"""Alarm ve uptime yardımcı fonksiyon testleri."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from health_check import alarm_var, kaydet, uptime_yuzde


class MetrikTestleri(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dosya = Path(self.tmp.name) / "tarihce.csv"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_alarm_uc_ulasilamiyor(self) -> None:
        for _ in range(3):
            kaydet("API", {"durum": "ULASILAMIYOR", "sure_ms": None, "kod": None}, self.dosya)
        self.assertTrue(alarm_var("API", dosya=self.dosya))

    def test_alarm_iki_yetersiz(self) -> None:
        for _ in range(2):
            kaydet("API", {"durum": "ULASILAMIYOR", "sure_ms": None, "kod": None}, self.dosya)
        self.assertFalse(alarm_var("API", dosya=self.dosya))

    def test_alarm_araya_saglikli_girerse_söner(self) -> None:
        kaydet("API", {"durum": "ULASILAMIYOR", "sure_ms": None, "kod": None}, self.dosya)
        kaydet("API", {"durum": "ULASILAMIYOR", "sure_ms": None, "kod": None}, self.dosya)
        kaydet("API", {"durum": "SAGLIKLI", "sure_ms": 100, "kod": 200}, self.dosya)
        self.assertFalse(alarm_var("API", dosya=self.dosya))

    def test_uptime_yuzde(self) -> None:
        kaydet("API", {"durum": "SAGLIKLI", "sure_ms": 100, "kod": 200}, self.dosya)
        kaydet("API", {"durum": "SAGLIKLI", "sure_ms": 120, "kod": 200}, self.dosya)
        kaydet("API", {"durum": "HATALI", "sure_ms": 50, "kod": 500}, self.dosya)
        kaydet("API", {"durum": "ULASILAMIYOR", "sure_ms": None, "kod": None}, self.dosya)
        self.assertEqual(uptime_yuzde("API", pencere=100, dosya=self.dosya), 50.0)

    def test_uptime_bos(self) -> None:
        self.assertIsNone(uptime_yuzde("API", dosya=self.dosya))


if __name__ == "__main__":
    unittest.main()
