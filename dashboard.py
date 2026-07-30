"""Sağlık Dashboard'u — Challenge 8 Görev 2: durum kartları."""

from datetime import datetime

import streamlit as st

from health_check import check

HEDEFLER = [
    {"ad": "Mini Envanter API", "url": "http://127.0.0.1:8000/health"},
    {
        "ad": "Open-Meteo",
        "url": "https://api.open-meteo.com/v1/forecast?latitude=41&longitude=29&current_weather=true",
    },
    {"ad": "RestCountries", "url": "https://restcountries.com/v3.1/alpha/tr"},
    {"ad": "Bozuk Hedef", "url": "http://localhost:9999/yok"},
]

DURUM_IKON = {
    "SAGLIKLI": "🟢",
    "YAVAS": "🟡",
    "HATALI": "🔴",
    "ULASILAMIYOR": "⚫",
}


st.set_page_config(page_title="Sağlık Dashboard", page_icon="💚", layout="wide")
st.title("Sağlık Dashboard'u")
st.caption("Mini NOC — servis health check ekranı")

if st.button("Şimdi Yenile", type="primary"):
    st.rerun()

kontrol_saati = datetime.now().strftime("%H:%M:%S")
st.write(f"Son kontrol: **{kontrol_saati}**")

sutunlar = st.columns(len(HEDEFLER))

for sutun, hedef in zip(sutunlar, HEDEFLER):
    sonuc = check(hedef["url"])
    ikon = DURUM_IKON.get(sonuc["durum"], "❓")
    sure = sonuc["sure_ms"]
    sure_yazi = f"{sure} ms" if sure is not None else "—"

    with sutun:
        st.subheader(f"{ikon} {hedef['ad']}")
        st.metric(label="Durum", value=sonuc["durum"])
        st.metric(label="Yanıt süresi", value=sure_yazi)
        kod = sonuc["kod"]
        st.caption(f"HTTP: {kod if kod is not None else 'yok'} · {kontrol_saati}")
