"""Metrik ve alarm yardımcıları için birim testleri."""

from __future__ import annotations

import unittest

from health_check import (
    HATALI,
    SAGLIKLI,
    ULASILAMIYOR,
    YAVAS,
    alarm_detay_metni,
    alarm_suresi_saniye,
    incident_log_kayitlari,
    operasyon_ozeti_hesapla,
    son_basari_zamani,
    son_hata_zamani,
    sure_formatla,
)


class TestOperasyonOzeti(unittest.TestCase):
    def test_operasyon_ozeti_hesapla(self) -> None:
        sonuclar = [
            {"durum": SAGLIKLI, "sure_ms": 120},
            {"durum": YAVAS, "sure_ms": 1500},
            {"durum": ULASILAMIYOR, "sure_ms": ""},
            {"durum": HATALI, "sure_ms": 80},
        ]
        ozet = operasyon_ozeti_hesapla(sonuclar)
        self.assertEqual(ozet["toplam"], 4)
        self.assertEqual(ozet["saglikli"], 1)
        self.assertEqual(ozet["yavas"], 1)
        self.assertEqual(ozet["hatali"], 1)
        self.assertEqual(ozet["ulasilamiyor"], 1)
        self.assertEqual(ozet["ortalama_sure_ms"], 566.7)


class TestIncidentLog(unittest.TestCase):
    def test_incident_log_alarm_etiketi(self) -> None:
        tarihce = [
            {"zaman": "2026-07-29 10:10:00", "hedef": "API", "durum": ULASILAMIYOR},
            {"zaman": "2026-07-29 10:11:00", "hedef": "API", "durum": ULASILAMIYOR},
            {"zaman": "2026-07-29 10:12:00", "hedef": "API", "durum": ULASILAMIYOR},
        ]
        incidents = incident_log_kayitlari(tarihce, limit=5, alarm_esigi=3)
        self.assertEqual(len(incidents), 3)
        self.assertEqual(incidents[0]["etiket"], "ALARM")
        self.assertEqual(incidents[0]["css"], "alarm")

    def test_incident_log_saglikli_kayitlari_atlar(self) -> None:
        tarihce = [
            {"zaman": "2026-07-29 10:10:00", "hedef": "API", "durum": SAGLIKLI},
            {"zaman": "2026-07-29 10:11:00", "hedef": "API", "durum": YAVAS},
        ]
        incidents = incident_log_kayitlari(tarihce)
        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents[0]["etiket"], YAVAS)


class TestAlarmDetay(unittest.TestCase):
    def test_alarm_detay_metni(self) -> None:
        tarihce = [
            {"zaman": "2026-07-29 10:10:00", "hedef": "API", "durum": ULASILAMIYOR},
            {"zaman": "2026-07-29 10:11:00", "hedef": "API", "durum": ULASILAMIYOR},
            {"zaman": "2026-07-29 10:12:00", "hedef": "API", "durum": ULASILAMIYOR},
        ]
        detay = alarm_detay_metni(tarihce, esik=3, yenileme_saniye=30)
        self.assertIsNotNone(detay)
        assert detay is not None
        self.assertIn("Son 3 kontrol ulaşılamadı", detay)
        self.assertIn("Süre:", detay)

    def test_alarm_suresi_saniye(self) -> None:
        tarihce = [
            {"zaman": "2026-07-29 10:10:00", "hedef": "API", "durum": ULASILAMIYOR},
            {"zaman": "2026-07-29 10:12:30", "hedef": "API", "durum": ULASILAMIYOR},
            {"zaman": "2026-07-29 10:15:00", "hedef": "API", "durum": ULASILAMIYOR},
        ]
        sure = alarm_suresi_saniye(tarihce, esik=3)
        self.assertEqual(sure, 300)

    def test_sure_formatla(self) -> None:
        self.assertEqual(sure_formatla(45), "45s")
        self.assertEqual(sure_formatla(154), "2m 34s")


class TestSonDurumZamanlari(unittest.TestCase):
    def test_son_basari_ve_hata_zamani(self) -> None:
        tarihce = [
            {"zaman": "2026-07-29 10:10:00", "hedef": "API", "durum": SAGLIKLI},
            {"zaman": "2026-07-29 10:11:00", "hedef": "API", "durum": YAVAS},
            {"zaman": "2026-07-29 10:12:00", "hedef": "API", "durum": SAGLIKLI},
            {"zaman": "2026-07-29 10:13:00", "hedef": "API", "durum": ULASILAMIYOR},
        ]
        self.assertEqual(son_basari_zamani(tarihce), "2026-07-29 10:12:00")
        self.assertEqual(son_hata_zamani(tarihce), "2026-07-29 10:13:00")


if __name__ == "__main__":
    unittest.main()
