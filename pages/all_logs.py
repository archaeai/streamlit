import streamlit as st

st.markdown("#all log ❄️")

conn = st.connection('mysql', type='sql')
# Perform query. 캐쉬 10분 설정 로직.
df = conn.query('SELECT * from trade_logs;', ttl=3000)

st.dataframe(df)