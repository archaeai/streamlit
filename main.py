import streamlit as st
import pandas as pd
import numpy as np



# DataFrame 생성
json_file_path = 'test.json'
df = pd.read_json(json_file_path, lines=True)
df['timestamp'] = pd.to_datetime(df['timestamp'])

# 시작 및 종료 timestamp 계산
start_timestamp = df['timestamp'].min()
end_timestamp = df['timestamp'].max()
# 사용자 목록 생성 (중복 제거)
user_list = df['user_id'].unique()


def determine_profit_loss(group):
    # 'main' 타입 주문 중 'open'과 'close' 상태의 주문 필터링
    open_order = group[(group['order_type'] == 'main') & (group['open_or_close'] == 'open')]
    close_order = group[(group['order_type'] == 'main') & (group['open_or_close'] == 'close')]

    # 'open'과 'close' 상태의 주문이 모두 있는지 확인
    if not open_order.empty and not close_order.empty:
        open_price = open_order['current_price'].iloc[0]
        close_price = close_order['current_price'].iloc[0]
        position = open_order['position'].iloc[0]

        if position == 'LONG':
            return 'profit' if close_price > open_price else 'loss'
        elif position == 'SHORT':
            return 'profit' if close_price < open_price else 'loss'
    if not open_order.empty and close_order.empty:
        return 'activate'

    if open_order.empty and not close_order.empty:
        return "open_empty"

    return 'unknown'  # 'open' 또는 'close' 주문이 누락된 경우


# split 주문 분석
def split_order_analysis(group, split_status, split_type):
    return len(group[(group['order_type'] == 'split') & (group['open_or_close'] == split_status) & (
                group['split_type'] == split_type)])


# orderId를 입력으로 받아 해당 orderId만 필터링하여 반환하는 함수

def filter_df(_df, key, filter_value):
    filtered_df = _df[_df[key] == filter_value]
    return filtered_df


def aggregate_results(group):
    return pd.Series({
        'symbol': group['symbol'].iloc[0],  # 첫 번째 symbol 값
        'position': group['position'].iloc[0],  # 첫 번째 position 값
        'profit_loss': determine_profit_loss(group),
        'split_open_water': split_order_analysis(group, 'open', 'water'),
        'split_close_water': split_order_analysis(group, 'close', 'water'),
        'split_open_bull': split_order_analysis(group, 'open', 'bull'),
        'split_close_bull': split_order_analysis(group, 'close', 'bull'),
    })


# apply 함수를 사용할 때 include_groups=False를 추가하거나 경고를 무시
results = df.groupby('order_id').apply(aggregate_results, include_groups=False).reset_index()
profit_or_lost_result = results[(results["profit_loss"] == "loss") | (results["profit_loss"] == "profit")]

if __name__=='__main__':
    st.title('Bot 2 청산된 주문 분석')
    # Streamlit selectbox를 사용하여 유저 선택
    selected_user = st.selectbox('유저 선택:', user_list)
    # 선택된 유저에 해당하는 데이터만 필터링
    df = df[df['user_id'] == selected_user]
    # apply 함수를 사용할 때 include_groups=False를 추가하거나 경고를 무시
    results = df.groupby('order_id').apply(aggregate_results, include_groups=False).reset_index()
    profit_or_lost_result = results[(results["profit_loss"] == "loss") | (results["profit_loss"] == "profit")]
    
    st.dataframe(profit_or_lost_result, use_container_width=True)
    # 시간 범위 표시
    st.write(f"데이터 시간 범위: {start_timestamp} 부터 {end_timestamp} 까지")
