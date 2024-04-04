import streamlit as st

st.markdown("# cancel log  ❄️")
conn = st.connection('mysql', type='sql')
# Perform query. 캐쉬 10분 설정 로직.
df = conn.query('SELECT * from cancel_logs;', ttl=300)

# 유저 리스트 가져오기
user_list = df['user_id'].unique()
selected_user = st.selectbox('유저 선택:', user_list)

filtered_df = df[df['user_id'] == selected_user]
st.dataframe(filtered_df)