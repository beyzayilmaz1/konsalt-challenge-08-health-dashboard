"""Sağlık Dashboard'u — Challenge 8: kartlar + tarihçe grafikleri."""

from datetime import datetime

import pandas as pd
import streamlit as st

from health_check import check, kaydet, tarihce_oku

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
    kaydet(hedef["ad"], sonuc)

    ikon = DURUM_IKON.get(sonuc["durum"], "❓")
    sure = sonuc["sure_ms"]
    sure_yazi = f"{sure} ms" if sure is not None else "—"

    with sutun:
        st.subheader(f"{ikon} {hedef['ad']}")
        st.metric(label="Durum", value=sonuc["durum"])
        st.metric(label="Yanıt süresi", value=sure_yazi)
        kod = sonuc["kod"]
        st.caption(f"HTTP: {kod if kod is not None else 'yok'} · {kontrol_saati}")

# --- Görev 3: yanıt süresi tarihçesi ---
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
