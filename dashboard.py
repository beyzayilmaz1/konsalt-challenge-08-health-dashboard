"""Sağlık Dashboard'u — Challenge 8: kartlar, özet, tarihçe, alarm, incident log."""

import json
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from health_check import (
    alarm_var,
    check,
    incident_log,
    kaydet,
    operasyon_ozeti,
    tarihce_oku,
    uptime_yuzde,
)

HEDEFLER_DOSYASI = Path("hedefler.json")


def hedefleri_yukle(dosya: Path = HEDEFLER_DOSYASI) -> list[dict]:
    """İzlenecek hedefleri JSON dosyasından okur."""
    with dosya.open(encoding="utf-8") as f:
        return json.load(f)


HEDEFLER = hedefleri_yukle()

DURUM_IKON = {
    "SAGLIKLI": "🟢",
    "YAVAS": "🟡",
    "HATALI": "🔴",
    "ULASILAMIYOR": "⚫",
}

YENILEME_SN = 30


st.set_page_config(page_title="Sağlık Dashboard", page_icon="💚", layout="wide")
st.title("Sağlık Dashboard'u")
st.caption("Mini NOC — servis health check ekranı")

with st.sidebar:
    st.header("Ayarlar")
    otomatik = st.toggle("Otomatik yenileme (30 sn)", value=True)
    if st.button("Şimdi Yenile", type="primary"):
        st.rerun()

kontrol_saati = datetime.now().strftime("%H:%M:%S")
st.write(f"Son kontrol: **{kontrol_saati}**")

anlik_sonuclar: list[dict] = []
sutunlar = st.columns(len(HEDEFLER))

for sutun, hedef in zip(sutunlar, HEDEFLER):
    sonuc = check(hedef["url"])
    kaydet(hedef["ad"], sonuc)
    alarm = alarm_var(hedef["ad"])
    uptime = uptime_yuzde(hedef["ad"])
    anlik_sonuclar.append(
        {"ad": hedef["ad"], "durum": sonuc["durum"], "sure_ms": sonuc["sure_ms"]}
    )

    ikon = DURUM_IKON.get(sonuc["durum"], "❓")
    sure = sonuc["sure_ms"]
    sure_yazi = f"{sure} ms" if sure is not None else "—"
    uptime_yazi = f"%{uptime}" if uptime is not None else "—"

    with sutun:
        if alarm:
            st.error("⚠ ALARM")
        st.subheader(f"{ikon} {hedef['ad']}")
        st.metric(label="Durum", value=sonuc["durum"])
        st.metric(label="Yanıt süresi", value=sure_yazi)
        st.metric(label="Uptime (son 100)", value=uptime_yazi)
        kod = sonuc["kod"]
        st.caption(f"HTTP: {kod if kod is not None else 'yok'} · {kontrol_saati}")

# Operasyon özeti
ozet = operasyon_ozeti(anlik_sonuclar)
st.divider()
st.subheader("Operasyon özeti")
o1, o2, o3, o4, o5, o6 = st.columns(6)
o1.metric("Servis", ozet["toplam"])
o2.metric("🟢 SAGLIKLI", ozet["dagilim"]["SAGLIKLI"])
o3.metric("🟡 YAVAS", ozet["dagilim"]["YAVAS"])
o4.metric("🔴 HATALI", ozet["dagilim"]["HATALI"])
o5.metric("⚫ ULASILAMIYOR", ozet["dagilim"]["ULASILAMIYOR"])
ort = ozet["ortalama_ms"]
o6.metric("Ort. süre", f"{ort} ms" if ort is not None else "—")

st.divider()
st.subheader("Yanıt süresi tarihçesi")

kayitlar = tarihce_oku()
if not kayitlar:
    st.info("Henüz kayıt yok. Yenile butonuna basarak kontrol biriktirin.")
else:
    df = pd.DataFrame(kayitlar)
    df["sure_ms"] = pd.to_numeric(df["sure_ms"], errors="coerce")

    grafik_sutunlari = st.columns(2)
    for i, hedef in enumerate(HEDEFLER):
        hedef_df = df[df["hedef"] == hedef["ad"]].copy()
        with grafik_sutunlari[i % 2]:
            st.markdown(f"**{hedef['ad']}**")
            if hedef_df.empty or hedef_df["sure_ms"].isna().all():
                st.caption("Çizilecek süre verisi yok (ULAŞILAMIYOR kayıtları süre tutmaz).")
            else:
                cizim = hedef_df[["zaman", "sure_ms"]].dropna().set_index("zaman")
                st.line_chart(cizim)

# Incident Log
st.divider()
st.subheader("Incident Log")
incidents = incident_log()
if not incidents:
    st.success("Sağlıksız olay yok.")
else:
    st.dataframe(pd.DataFrame(incidents), use_container_width=True, hide_index=True)

if otomatik:
    st.caption(f"Otomatik yenileme açık — {YENILEME_SN} sn sonra tekrar kontrol edilecek.")
    time.sleep(YENILEME_SN)
    st.rerun()
