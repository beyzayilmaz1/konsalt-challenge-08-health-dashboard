"""
KONSALT Challenge 8 — Sağlık Dashboard'u (mini NOC ekranı)

Periyodik health check + durum kartları + yanıt süresi tarihçesi + alarm.
Hedef listesi hedefler.json üzerinden yönetilir (configuration management).
"""

from __future__ import annotations

import csv
import html
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from health_check import (
    DURUM_IKON,
    HATALI,
    SAGLIKLI,
    ULASILAMIYOR,
    YAVAS,
    alarm_detay_metni,
    ardisik_ulasilamiyor_mu,
    check,
    incident_log_kayitlari,
    operasyon_ozeti_hesapla,
    son_basari_zamani,
    son_hata_zamani,
    uptime_yuzdesi,
)

BASE_DIR = Path(__file__).resolve().parent
HEDEFLER_DOSYASI = BASE_DIR / "hedefler.json"
TARIHCE_DOSYASI = BASE_DIR / "tarihce.csv"
YENILEME_SANIYE = 30
ALARM_ESIGI = 3
UPTIME_PENCERE = 100
INCIDENT_LIMIT = 12

CSV_ALANLAR = ["zaman", "hedef", "url", "durum", "sure_ms", "kod"]

st.set_page_config(
    page_title="Konsalt Sağlık Dashboard",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

:root {
  --bg-0: #0b1220;
  --bg-1: #121a2b;
  --bg-2: #182338;
  --ink: #e8eef8;
  --muted: #8b9bb4;
  --line: rgba(232, 238, 248, 0.10);
  --accent: #2dd4bf;
  --accent-2: #38bdf8;
  --ok: #34d399;
  --warn: #fbbf24;
  --bad: #f87171;
  --down: #94a3b8;
  --card: rgba(18, 26, 43, 0.88);
  --shadow: 0 18px 50px rgba(0, 0, 0, 0.35);
  --radius: 18px;
}

html, body, [class*="css"] {
  font-family: "IBM Plex Sans", sans-serif !important;
}

.stApp {
  background:
    radial-gradient(1200px 600px at 8% -10%, rgba(45, 212, 191, 0.18), transparent 55%),
    radial-gradient(900px 500px at 92% 0%, rgba(56, 189, 248, 0.16), transparent 50%),
    linear-gradient(165deg, var(--bg-0) 0%, var(--bg-1) 48%, #0e1626 100%) !important;
  color: var(--ink);
}

.stApp::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  opacity: 0.22;
  background-image:
    linear-gradient(rgba(232, 238, 248, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(232, 238, 248, 0.04) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: radial-gradient(ellipse at center, black 35%, transparent 80%);
  z-index: 0;
}

[data-testid="stHeader"] {
  background: rgba(11, 18, 32, 0.55) !important;
  backdrop-filter: blur(10px);
}

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0d1524 0%, #111b2e 100%) !important;
  border-right: 1px solid var(--line);
}

[data-testid="stSidebar"] * {
  color: var(--ink) !important;
}

[data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] small {
  color: var(--muted) !important;
}

.block-container {
  padding-top: 1.4rem !important;
  padding-bottom: 2.5rem !important;
  max-width: 1400px;
}

.hero {
  position: relative;
  margin: 0 0 1.35rem 0;
  padding: 1.35rem 1.5rem 1.45rem;
  border: 1px solid var(--line);
  border-radius: 22px;
  background:
    linear-gradient(135deg, rgba(45, 212, 191, 0.10), rgba(56, 189, 248, 0.05) 40%, rgba(18, 26, 43, 0.65)),
    var(--card);
  box-shadow: var(--shadow);
  overflow: hidden;
  animation: fade-up 0.55s ease both;
}

.hero::after {
  content: "";
  position: absolute;
  right: -40px;
  top: -40px;
  width: 220px;
  height: 220px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(45, 212, 191, 0.28), transparent 70%);
  pointer-events: none;
}

.hero-kicker {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  font-family: "Space Grotesk", sans-serif;
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--accent);
  margin-bottom: 0.55rem;
}

.hero h1 {
  font-family: "Space Grotesk", sans-serif !important;
  font-size: clamp(1.85rem, 3vw, 2.55rem) !important;
  font-weight: 700 !important;
  letter-spacing: -0.03em;
  margin: 0 0 0.45rem 0 !important;
  color: var(--ink) !important;
  line-height: 1.1 !important;
}

.hero p {
  margin: 0;
  max-width: 62ch;
  color: var(--muted);
  font-size: 1.02rem;
  line-height: 1.5;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 0 0 rgba(45, 212, 191, 0.55);
  animation: pulse 1.8s infinite;
}

.stat-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.75rem;
  margin: 0 0 1.15rem 0;
  animation: fade-up 0.65s ease both;
}

.stat-pill {
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 0.85rem 1rem;
  background: rgba(18, 26, 43, 0.72);
  backdrop-filter: blur(8px);
}

.stat-pill .label {
  font-size: 0.72rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
  font-weight: 600;
}

.stat-pill .value {
  font-family: "Space Grotesk", sans-serif;
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--ink);
  margin-top: 0.2rem;
}

.alarm-banner {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  margin: 0 0 1.1rem 0;
  padding: 0.95rem 1.15rem;
  border-radius: 14px;
  border: 1px solid rgba(248, 113, 113, 0.45);
  background: linear-gradient(90deg, rgba(248, 113, 113, 0.18), rgba(251, 191, 36, 0.08));
  color: #fecaca;
  font-weight: 600;
  animation: alarm-in 0.45s ease both, alarm-glow 2.2s ease-in-out infinite;
}

.alarm-banner .badge {
  font-family: "Space Grotesk", sans-serif;
  font-size: 0.75rem;
  letter-spacing: 0.1em;
  padding: 0.28rem 0.55rem;
  border-radius: 8px;
  background: rgba(248, 113, 113, 0.28);
  border: 1px solid rgba(248, 113, 113, 0.45);
}

.noc-card {
  position: relative;
  height: 100%;
  min-height: 260px;
  padding: 1.15rem 1.1rem 1.05rem;
  border-radius: var(--radius);
  border: 1px solid var(--line);
  background: linear-gradient(180deg, rgba(24, 35, 56, 0.95), rgba(14, 22, 38, 0.92));
  box-shadow: var(--shadow);
  overflow: hidden;
  transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
  animation: fade-up 0.7s ease both;
}

.noc-card:hover {
  transform: translateY(-3px);
  border-color: rgba(45, 212, 191, 0.35);
  box-shadow: 0 22px 55px rgba(0, 0, 0, 0.42);
}

.noc-card .accent {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
}

.noc-card.ok .accent { background: linear-gradient(180deg, var(--ok), #059669); }
.noc-card.warn .accent { background: linear-gradient(180deg, var(--warn), #d97706); }
.noc-card.bad .accent { background: linear-gradient(180deg, var(--bad), #dc2626); }
.noc-card.down .accent { background: linear-gradient(180deg, var(--down), #475569); }

.noc-card .top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.5rem;
  margin-bottom: 0.85rem;
}

.noc-card .name {
  font-family: "Space Grotesk", sans-serif;
  font-weight: 700;
  font-size: 1.05rem;
  letter-spacing: -0.02em;
  color: var(--ink);
  line-height: 1.25;
}

.noc-card .status {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  margin: 0.35rem 0 0.95rem;
  font-family: "Space Grotesk", sans-serif;
  font-weight: 700;
  font-size: 0.95rem;
  letter-spacing: 0.04em;
}

.noc-card.ok .status { color: var(--ok); }
.noc-card.warn .status { color: var(--warn); }
.noc-card.bad .status { color: var(--bad); }
.noc-card.down .status { color: var(--down); }

.metrics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.65rem;
  margin-bottom: 0.85rem;
}

.metric {
  border-radius: 12px;
  border: 1px solid var(--line);
  background: rgba(11, 18, 32, 0.55);
  padding: 0.65rem 0.7rem;
}

.metric .m-label {
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
  font-weight: 600;
}

.metric .m-value {
  font-family: "Space Grotesk", sans-serif;
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--ink);
  margin-top: 0.15rem;
}

.meta {
  font-size: 0.82rem;
  color: var(--muted);
  line-height: 1.45;
}

.card-alarm {
  display: block;
  text-align: center;
  margin-bottom: 0.85rem;
  padding: 0.7rem 0.85rem;
  border-radius: 12px;
  font-family: "Space Grotesk", sans-serif;
  font-size: 1.2rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  color: #fecaca;
  background: linear-gradient(90deg, rgba(248, 113, 113, 0.28), rgba(251, 191, 36, 0.12));
  border: 1px solid rgba(248, 113, 113, 0.55);
  box-shadow: 0 0 24px rgba(248, 113, 113, 0.25);
  animation: pulse 1.6s infinite, alarm-glow 2.2s ease-in-out infinite;
}

.alarm-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  margin-bottom: 0.7rem;
  padding: 0.35rem 0.65rem;
  border-radius: 999px;
  font-family: "Space Grotesk", sans-serif;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: #fecaca;
  background: rgba(248, 113, 113, 0.18);
  border: 1px solid rgba(248, 113, 113, 0.45);
  animation: pulse 1.6s infinite;
}

.section-head {
  margin: 1.5rem 0 0.85rem;
  padding-top: 0.35rem;
  animation: fade-up 0.75s ease both;
}

.section-head h2 {
  font-family: "Space Grotesk", sans-serif !important;
  font-size: 1.35rem !important;
  font-weight: 700 !important;
  letter-spacing: -0.02em;
  margin: 0 0 0.25rem 0 !important;
  color: var(--ink) !important;
}

.section-head p {
  margin: 0;
  color: var(--muted);
  font-size: 0.92rem;
}

.chart-shell {
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 0.85rem 0.9rem 0.35rem;
  background: rgba(18, 26, 43, 0.72);
  margin-bottom: 0.85rem;
}

.chart-shell .title {
  font-family: "Space Grotesk", sans-serif;
  font-weight: 600;
  font-size: 0.95rem;
  color: var(--ink);
  margin-bottom: 0.35rem;
}

.ops-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 0.75rem;
  margin-bottom: 0.95rem;
  animation: fade-up 0.75s ease both;
}

.ops-card {
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 0.9rem 1rem;
  background: rgba(18, 26, 43, 0.72);
  backdrop-filter: blur(8px);
}

.ops-card .label {
  font-size: 0.72rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
  font-weight: 600;
}

.ops-card .value {
  font-family: "Space Grotesk", sans-serif;
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--ink);
  margin-top: 0.2rem;
}

.ops-card.ok .value { color: var(--ok); }
.ops-card.warn .value { color: var(--warn); }
.ops-card.bad .value { color: var(--bad); }
.ops-card.down .value { color: var(--down); }

.incident-shell {
  border: 1px solid var(--line);
  border-radius: 16px;
  background: rgba(18, 26, 43, 0.72);
  overflow: hidden;
  animation: fade-up 0.8s ease both;
}

.incident-row {
  display: grid;
  grid-template-columns: 185px minmax(0, 1fr) 170px;
  gap: 0.8rem;
  align-items: center;
  padding: 0.9rem 1rem;
  border-bottom: 1px solid var(--line);
}

.incident-row:last-child {
  border-bottom: 0;
}

.incident-time {
  color: var(--muted);
  font-size: 0.86rem;
}

.incident-service {
  font-family: "Space Grotesk", sans-serif;
  font-weight: 600;
  color: var(--ink);
}

.incident-badge {
  justify-self: end;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 132px;
  padding: 0.42rem 0.75rem;
  border-radius: 999px;
  font-family: "Space Grotesk", sans-serif;
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.06em;
}

.incident-badge.warn {
  color: #fef3c7;
  background: rgba(251, 191, 36, 0.16);
  border: 1px solid rgba(251, 191, 36, 0.38);
}

.incident-badge.bad {
  color: #fecaca;
  background: rgba(248, 113, 113, 0.16);
  border: 1px solid rgba(248, 113, 113, 0.38);
}

.incident-badge.down {
  color: #cbd5e1;
  background: rgba(148, 163, 184, 0.14);
  border: 1px solid rgba(148, 163, 184, 0.35);
}

.incident-badge.alarm {
  color: #fecaca;
  background: linear-gradient(90deg, rgba(248, 113, 113, 0.24), rgba(251, 191, 36, 0.12));
  border: 1px solid rgba(248, 113, 113, 0.48);
}

.sla-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.75rem;
  margin-bottom: 0.95rem;
  animation: fade-up 0.78s ease both;
}

.sla-card {
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 0.9rem 1rem;
  background: rgba(18, 26, 43, 0.72);
}

.sla-card .service {
  font-family: "Space Grotesk", sans-serif;
  font-weight: 600;
  color: var(--ink);
  margin-bottom: 0.35rem;
}

.sla-card .uptime {
  font-family: "Space Grotesk", sans-serif;
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--ink);
}

.sla-card.ok .uptime { color: var(--ok); }
.sla-card.warn .uptime { color: var(--warn); }
.sla-card.bad .uptime { color: var(--bad); }
.sla-card.down .uptime { color: var(--down); }

.sla-card .meta {
  margin-top: 0.25rem;
  font-size: 0.82rem;
  color: var(--muted);
}

.card-alarm-detail {
  margin-bottom: 0.75rem;
  padding: 0.55rem 0.7rem;
  border-radius: 10px;
  font-size: 0.8rem;
  color: #fecaca;
  background: rgba(248, 113, 113, 0.12);
  border: 1px solid rgba(248, 113, 113, 0.28);
}

div[data-testid="stMetricValue"] {
  font-family: "Space Grotesk", sans-serif !important;
  color: var(--ink) !important;
}

div[data-testid="stMetricLabel"] {
  color: var(--muted) !important;
}

div[data-testid="stMetricDelta"] {
  color: var(--accent) !important;
}

div[data-testid="stMetric"] {
  background: rgba(18, 26, 43, 0.72);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 0.75rem 0.85rem;
}

.stButton > button {
  border-radius: 12px !important;
  font-family: "Space Grotesk", sans-serif !important;
  font-weight: 600 !important;
  border: 1px solid rgba(45, 212, 191, 0.35) !important;
  background: linear-gradient(135deg, #14b8a6, #0d9488) !important;
  color: #042f2e !important;
  box-shadow: 0 8px 24px rgba(20, 184, 166, 0.25) !important;
}

.stButton > button:hover {
  transform: translateY(-1px);
  box-shadow: 0 12px 28px rgba(20, 184, 166, 0.35) !important;
}

[data-testid="stDataFrame"] {
  border: 1px solid var(--line);
  border-radius: 14px;
  overflow: hidden;
  background: rgba(18, 26, 43, 0.88) !important;
}

[data-testid="stDataFrame"] *,
[data-testid="stDataFrame"] div,
[data-testid="stDataFrame"] span,
[data-testid="stDataFrame"] p {
  color: var(--ink) !important;
  background-color: transparent !important;
}

[data-testid="stDataFrame"] [role="grid"],
[data-testid="stDataFrame"] [role="row"],
[data-testid="stDataFrame"] [role="columnheader"],
[data-testid="stDataFrame"] [role="gridcell"] {
  background-color: rgba(14, 22, 38, 0.92) !important;
  border-color: var(--line) !important;
  color: var(--ink) !important;
}

[data-testid="stDataFrame"] [role="columnheader"] {
  background-color: rgba(24, 35, 56, 0.98) !important;
  color: var(--muted) !important;
  font-weight: 600 !important;
}

@keyframes fade-up {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(45, 212, 191, 0.55); }
  70% { box-shadow: 0 0 0 10px rgba(45, 212, 191, 0); }
  100% { box-shadow: 0 0 0 0 rgba(45, 212, 191, 0); }
}

@keyframes alarm-in {
  from { opacity: 0; transform: translateY(-6px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes alarm-glow {
  0%, 100% { filter: brightness(1); }
  50% { filter: brightness(1.08); }
}

@media (max-width: 1100px) {
  div[data-testid="stHorizontalBlock"] {
    flex-wrap: wrap !important;
    gap: 0.75rem !important;
  }
  div[data-testid="column"] {
    flex: 1 1 calc(50% - 0.75rem) !important;
    min-width: min(100%, 280px) !important;
  }
}

@media (max-width: 900px) {
  .stat-strip { grid-template-columns: 1fr; }
  .ops-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .hero h1 { font-size: 1.65rem !important; }
  .hero p { font-size: 0.95rem; }
}

@media (max-width: 640px) {
  div[data-testid="column"] {
    flex: 1 1 100% !important;
    width: 100% !important;
  }
  .noc-card {
    min-height: auto;
    padding: 1rem 0.95rem;
  }
  .metrics { grid-template-columns: 1fr; }
  .block-container {
    padding-left: 0.85rem !important;
    padding-right: 0.85rem !important;
  }
  .alarm-banner {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  .ops-grid { grid-template-columns: 1fr; }
  .incident-row {
    grid-template-columns: 1fr;
    align-items: flex-start;
  }
  .incident-badge {
    justify-self: start;
  }
}
</style>
"""


def inject_theme() -> None:
    st.markdown(THEME_CSS, unsafe_allow_html=True)


def render_html(markup: str) -> None:
    """Markdown yerine doğrudan HTML render — uzun özel bloklarda daha güvenilir."""
    st.html(markup)


def hedefleri_yukle() -> list[dict[str, str]]:
    if not HEDEFLER_DOSYASI.exists():
        st.error(f"`{HEDEFLER_DOSYASI.name}` bulunamadı.")
        return []
    data = json.loads(HEDEFLER_DOSYASI.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        st.error("hedefler.json boş veya geçersiz.")
        return []
    return data


def tarihce_yukle() -> list[dict[str, Any]]:
    if not TARIHCE_DOSYASI.exists():
        return []
    with TARIHCE_DOSYASI.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def tarihceye_ekle(satirlar: list[dict[str, Any]]) -> None:
    dosya_yeni = not TARIHCE_DOSYASI.exists()
    with TARIHCE_DOSYASI.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_ALANLAR)
        if dosya_yeni:
            writer.writeheader()
        for satir in satirlar:
            writer.writerow(satir)


def hedef_kayitlari(tarihce: list[dict[str, Any]], hedef_adi: str) -> list[dict[str, Any]]:
    return [k for k in tarihce if k.get("hedef") == hedef_adi]


def durum_sinifi(durum: str) -> str:
    return {
        SAGLIKLI: "ok",
        YAVAS: "warn",
        HATALI: "bad",
        ULASILAMIYOR: "down",
    }.get(durum, "down")


def uptime_sinifi(uptime: float | None) -> str:
    if uptime is None:
        return "down"
    if uptime >= 95:
        return "ok"
    if uptime >= 70:
        return "warn"
    return "bad"


def kontrolleri_calistir(hedefler: list[dict[str, str]]) -> list[dict[str, Any]]:
    sonuclar: list[dict[str, Any]] = []
    zaman = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for hedef in hedefler:
        sonuc = check(hedef["url"])
        kayit = {
            "zaman": zaman,
            "hedef": hedef["ad"],
            "url": hedef["url"],
            "durum": sonuc["durum"],
            "sure_ms": "" if sonuc["sure_ms"] is None else sonuc["sure_ms"],
            "kod": "" if sonuc["kod"] is None else sonuc["kod"],
        }
        sonuclar.append({**kayit, "_raw": sonuc})
    tarihceye_ekle(
        [
            {
                "zaman": s["zaman"],
                "hedef": s["hedef"],
                "url": s["url"],
                "durum": s["durum"],
                "sure_ms": s["sure_ms"],
                "kod": s["kod"],
            }
            for s in sonuclar
        ]
    )
    return sonuclar


def sidebar(hedefler: list[dict[str, str]], tarihce: list[dict[str, Any]]) -> None:
    st.sidebar.markdown("### Kontrol Paneli")
    st.sidebar.caption("KONSALT Challenge 8 · Mini NOC")

    if st.sidebar.button("Şimdi Yenile", type="primary", use_container_width=True):
        st.rerun()

    if "auto_refresh" not in st.session_state:
        query_auto = st.query_params.get("auto", "1")
        st.session_state["auto_refresh"] = query_auto not in {"0", "false", "False"}
    st.sidebar.toggle("Otomatik yenileme (30 sn)", key="auto_refresh")

    st.sidebar.markdown("---")
    st.sidebar.subheader("Hedefler")
    st.sidebar.caption(f"`{HEDEFLER_DOSYASI.name}` — kod değiştirmeden yeni hedef ekleyin.")
    for h in hedefler:
        st.sidebar.markdown(f"- **{h['ad']}**")
        if h.get("aciklama"):
            st.sidebar.caption(h["aciklama"])

    st.sidebar.markdown("---")
    genel_uptime = uptime_yuzdesi(tarihce, UPTIME_PENCERE)
    st.sidebar.metric(
        "Genel uptime (son 100)",
        "—" if genel_uptime is None else f"%{genel_uptime}",
    )
    st.sidebar.caption(f"Toplam kayıt: {len(tarihce)}")
    st.sidebar.caption(f"Yenileme aralığı: {YENILEME_SANIYE} sn")


def kart_html(
    hedef: dict[str, str],
    sonuc: dict[str, Any],
    tarihce: list[dict[str, Any]],
) -> str:
    ad = hedef["ad"]
    durum = sonuc["durum"]
    ikon = DURUM_IKON.get(durum, "❓")
    raw = sonuc["_raw"]
    hedef_hist = hedef_kayitlari(tarihce, ad)
    alarm = ardisik_ulasilamiyor_mu(hedef_hist, ALARM_ESIGI)
    uptime = uptime_yuzdesi(hedef_hist, UPTIME_PENCERE)
    sure = raw["sure_ms"]
    sure_txt = "—" if sure is None else f"{sure:.0f} ms"
    kod_txt = "—" if raw["kod"] is None else str(raw["kod"])
    uptime_txt = (
        f"Uptime (son {min(len(hedef_hist), UPTIME_PENCERE)}): %{uptime}"
        if uptime is not None
        else "Uptime: —"
    )
    hata_txt = f"<div class='meta'>Hata tipi: <code>{raw['hata']}</code></div>" if raw.get("hata") else ""
    alarm_detay = alarm_detay_metni(hedef_hist, ALARM_ESIGI, YENILEME_SANIYE)
    alarm_txt = "<div class='card-alarm'>⚠ ALARM</div>" if alarm else ""
    alarm_detay_txt = (
        f"<div class='card-alarm-detail'>{alarm_detay}</div>" if alarm and alarm_detay else ""
    )
    son_basari = son_basari_zamani(hedef_hist)
    son_hata = son_hata_zamani(hedef_hist)
    son_basari_txt = f"<div class='meta'>Son başarılı kontrol: {son_basari}</div>" if son_basari else ""
    son_hata_txt = f"<div class='meta'>Son hatalı kontrol: {son_hata}</div>" if son_hata else ""
    css = durum_sinifi(durum)

    return f"""
    <div class="noc-card {css}">
      <div class="accent"></div>
      {alarm_txt}
      {alarm_detay_txt}
      <div class="top">
        <div class="name">{ad}</div>
      </div>
      <div class="status">{ikon} {durum}</div>
      <div class="metrics">
        <div class="metric">
          <div class="m-label">Yanıt süresi</div>
          <div class="m-value">{sure_txt}</div>
        </div>
        <div class="metric">
          <div class="m-label">HTTP kodu</div>
          <div class="m-value">{kod_txt}</div>
        </div>
      </div>
      <div class="meta">Son kontrol: {sonuc['zaman']}</div>
      <div class="meta">{uptime_txt}</div>
      {son_basari_txt}
      {son_hata_txt}
      {hata_txt}
    </div>
    """


def kart_ciz(
    col: Any,
    hedef: dict[str, str],
    sonuc: dict[str, Any],
    tarihce: list[dict[str, Any]],
) -> None:
    with col:
        st.markdown(kart_html(hedef, sonuc, tarihce), unsafe_allow_html=True)


def grafikleri_ciz(tarihce: list[dict[str, Any]], hedefler: list[dict[str, str]]) -> None:
    st.markdown(
        """
        <div class="section-head">
          <h2>Yanıt süresi tarihçesi</h2>
          <p>Her kontrol sonucu <code>tarihce.csv</code> dosyasına eklenir; veri biriktikçe grafik uzar.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if len(tarihce) < 2:
        st.info("Grafik için en az birkaç kontrol kaydı gerekir. Otomatik yenileme açıkken veri birikecektir.")
        return

    df = pd.DataFrame(tarihce)
    df["sure_ms"] = pd.to_numeric(df["sure_ms"], errors="coerce")
    df["zaman"] = pd.to_datetime(df["zaman"], errors="coerce")

    cols = st.columns(2)
    for idx, hedef in enumerate(hedefler):
        subset = df[df["hedef"] == hedef["ad"]].dropna(subset=["sure_ms"]).copy()
        with cols[idx % 2]:
            st.markdown(f"<div class='chart-shell'><div class='title'>{hedef['ad']}</div>", unsafe_allow_html=True)
            if subset.empty:
                st.caption("Henüz ölçülebilir süre yok (ULASILAMIYOR kayıtlarında süre boştur).")
            else:
                st.caption(f"{len(subset)} ölçüm noktası — veri biriktikçe grafik uzar.")
                chart_df = subset.set_index("zaman")[["sure_ms"]].rename(columns={"sure_ms": "ms"})
                st.line_chart(chart_df, height=220)
            st.markdown("</div>", unsafe_allow_html=True)


def ozet_tablo(sonuclar: list[dict[str, Any]]) -> None:
    st.markdown(
        """
        <div class="section-head">
          <h2>Bu tur özeti</h2>
          <p>Son probe turunun anlık sonuçları.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    tablo = pd.DataFrame(
        [
            {
                "Hedef": s["hedef"],
                "Durum": f"{DURUM_IKON.get(s['durum'], '')} {s['durum']}",
                "Süre (ms)": s["sure_ms"] if s["sure_ms"] != "" else "—",
                "Kod": s["kod"] if s["kod"] != "" else "—",
                "Zaman": s["zaman"],
            }
            for s in sonuclar
        ]
    )
    st.dataframe(tablo, use_container_width=True, hide_index=True)


def hero_ve_ozet(
    tarihce: list[dict[str, Any]],
    sonuclar: list[dict[str, Any]],
    aktif_alarm: bool,
) -> None:
    genel_uptime = uptime_yuzdesi(tarihce, UPTIME_PENCERE)
    saglikli = sum(1 for s in sonuclar if s["durum"] == SAGLIKLI)
    st.markdown(
        f"""
        <div class="hero">
          <div class="hero-kicker"><span class="pulse-dot"></span> Canlı NOC · KONSALT Challenge 8</div>
          <h1>Konsalt Sağlık Dashboard</h1>
          <p>Operasyon ekipleri için mini NOC ekranı — health check, latency ve alarm eşiği tek bakışta.</p>
        </div>
        <div class="stat-strip">
          <div class="stat-pill">
            <div class="label">Genel uptime</div>
            <div class="value">{"—" if genel_uptime is None else f"%{genel_uptime}"}</div>
          </div>
          <div class="stat-pill">
            <div class="label">Bu tur sağlıklı</div>
            <div class="value">{saglikli}/{len(sonuclar)}</div>
          </div>
          <div class="stat-pill">
            <div class="label">Tarihçe kaydı</div>
            <div class="value">{len(tarihce)}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if aktif_alarm:
        st.markdown(
            """
            <div class="alarm-banner">
              <span class="badge">ALARM</span>
              <span>En az bir hedef üst üste 3 kontrol boyunca ULASILAMIYOR. Kartlarda süre ve ardışık başarısız kontrol sayısı gösterilir.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def sla_uptime_goster(hedefler: list[dict[str, str]], tarihce: list[dict[str, Any]]) -> None:
    kartlar: list[str] = []
    for hedef in hedefler:
        hedef_hist = hedef_kayitlari(tarihce, hedef["ad"])
        uptime = uptime_yuzdesi(hedef_hist, UPTIME_PENCERE)
        pencere = min(len(hedef_hist), UPTIME_PENCERE)
        uptime_txt = "—" if uptime is None else f"%{uptime}"
        ad = html.escape(hedef["ad"])
        css = uptime_sinifi(uptime)
        kartlar.append(
            f'<div class="sla-card {css}">'
            f'<div class="service">{ad}</div>'
            f'<div class="uptime">{uptime_txt}</div>'
            f'<div class="meta">Son {pencere} kontrol · SAGLIKLI oranı</div>'
            "</div>"
        )

    render_html(
        '<div class="section-head">'
        "<h2>Servis SLA özeti</h2>"
        "<p>Her hedef için son kontrollerdeki sağlıklı probe oranı (uptime).</p>"
        "</div>"
        f'<div class="sla-grid">{"".join(kartlar)}</div>'
    )


def incident_log_goster(incidents: list[dict[str, str]]) -> None:
    render_html(
        '<div class="section-head">'
        "<h2>Incident Log</h2>"
        "<p>Sağlıksız, yavaş veya alarmlı olayların kronolojik geçmişi.</p>"
        "</div>"
    )
    if not incidents:
        st.success("Henüz incident kaydı yok. Tüm servisler sağlıklı akıyor.")
        return

    rows = "".join(
        '<div class="incident-row">'
        f'<div class="incident-time">{html.escape(incident["zaman"])}</div>'
        f'<div class="incident-service">{html.escape(incident["hedef"])}</div>'
        f'<div class="incident-badge {html.escape(incident["css"])}">{html.escape(incident["etiket"])}</div>'
        "</div>"
        for incident in incidents
    )
    render_html(f'<div class="incident-shell">{rows}</div>')


def operasyon_ozeti_goster(sonuclar: list[dict[str, Any]]) -> None:
    ozet = operasyon_ozeti_hesapla(sonuclar)
    ortalama_sure = "—" if ozet["ortalama_sure_ms"] is None else f"{ozet['ortalama_sure_ms']:.1f} ms"
    st.markdown(
        f"""
        <div class="section-head">
          <h2>Operasyon özeti</h2>
          <p>Mevcut turdaki servis dağılımı ve ortalama yanıt süresi.</p>
        </div>
        <div class="ops-grid">
          <div class="ops-card">
            <div class="label">Toplam servis</div>
            <div class="value">{ozet['toplam']}</div>
          </div>
          <div class="ops-card ok">
            <div class="label">Sağlıklı</div>
            <div class="value">{ozet['saglikli']}</div>
          </div>
          <div class="ops-card warn">
            <div class="label">Yavaş</div>
            <div class="value">{ozet['yavas']}</div>
          </div>
          <div class="ops-card bad">
            <div class="label">Hatalı</div>
            <div class="value">{ozet['hatali']}</div>
          </div>
          <div class="ops-card down">
            <div class="label">Ulaşılamıyor</div>
            <div class="value">{ozet['ulasilamiyor']}</div>
          </div>
          <div class="ops-card">
            <div class="label">Ort. yanıt süresi</div>
            <div class="value">{ortalama_sure}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    inject_theme()

    hedefler = hedefleri_yukle()
    if not hedefler:
        st.stop()

    sonuclar = kontrolleri_calistir(hedefler)
    tarihce = tarihce_yukle()
    sidebar(hedefler, tarihce)

    aktif_alarm = any(
        ardisik_ulasilamiyor_mu(hedef_kayitlari(tarihce, h["ad"]), ALARM_ESIGI) for h in hedefler
    )
    hero_ve_ozet(tarihce, sonuclar, aktif_alarm)
    operasyon_ozeti_goster(sonuclar)
    sla_uptime_goster(hedefler, tarihce)

    st.markdown(
        """
        <div class="section-head">
          <h2>Durum kartları</h2>
          <p>Her hedef için anlık probe sonucu — servis adı, renkli durum, yanıt süresi ve son kontrol saati.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    btn_sol, btn_sag = st.columns([3, 1])
    with btn_sag:
        if st.button("Şimdi Yenile", type="primary", use_container_width=True, key="yenile_ana"):
            st.rerun()

    # Challenge gereksinimi: st.metric — kartların üstünde kısa özet satırı
    metrik_kolonlar = st.columns(len(hedefler), gap="small")
    for col, hedef, sonuc in zip(metrik_kolonlar, hedefler, sonuclar):
        raw = sonuc["_raw"]
        ikon = DURUM_IKON.get(sonuc["durum"], "")
        sure_deger = "—" if raw["sure_ms"] is None else f"{raw['sure_ms']:.0f} ms"
        with col:
            st.metric(
                label=f"{ikon} {hedef['ad']}",
                value=sonuc["durum"],
                delta=sure_deger,
                delta_color="off",
            )

    kolonlar = st.columns(len(hedefler), gap="medium")
    for col, hedef, sonuc in zip(kolonlar, hedefler, sonuclar):
        kart_ciz(col, hedef, sonuc, tarihce)

    ozet_tablo(sonuclar)
    incidents = incident_log_kayitlari(tarihce, limit=INCIDENT_LIMIT, alarm_esigi=ALARM_ESIGI)
    incident_log_goster(incidents)
    grafikleri_ciz(tarihce, hedefler)

    with st.expander("Sağlık kuralları (özet)"):
        st.markdown(
            """
| Durum | Koşul |
|-------|--------|
| 🟢 **SAGLIKLI** | HTTP 2xx ve yanıt süresi &lt; 1 sn |
| 🟡 **YAVAS** | HTTP 2xx ama yanıt süresi ≥ 1 sn |
| 🔴 **HATALI** | HTTP 4xx / 5xx |
| ⚫ **ULASILAMIYOR** | Bağlantı hatası / timeout (status kodu yok) |

**Alarm:** Aynı hedefte ardışık 3 kontrol `ULASILAMIYOR` → kart üstünde ⚠ ALARM.
            """
        )

    if st.session_state.get("auto_refresh", True):
        time.sleep(YENILEME_SANIYE)
        st.rerun()


if __name__ == "__main__":
    main()
