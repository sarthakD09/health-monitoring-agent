import streamlit as st

st.set_page_config(page_title="Health Monitoring Agent", layout="wide")
st.title("Personalized & Context-Aware Health Monitoring Agent")
st.caption("Prototype dashboard — research use only; not a medical device.")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Heart Rate", "-- BPM")
c2.metric("SpO₂", "-- %")
c3.metric("Temperature", "-- °C")
c4.metric("State", "MONITOR")

st.info("Dashboard scaffold ready. Connect a replay adapter or live ESP32 adapter to populate the canonical observation stream.")
