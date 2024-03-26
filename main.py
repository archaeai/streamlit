import streamlit as st
import pandas as pd
import numpy as np


def load_and_preprocess_data(filepath):
    """데이터 로드 및 전처리를 수행하는 함수."""
    df = pd.read_json(filepath, lines=True)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df


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


def split_order_analysis(group, split_status, split_type):
    return len(group[(group['order_type'] == 'split') & (group['open_or_close'] == split_status) & (
            group['split_type'] == split_type)])


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


def get_user_filtered_results(df, user_id):
    """선택된 사용자의 데이터를 필터링하고 결과를 반환하는 함수."""
    filtered_df = df[df['user_id'] == user_id]
    results = filtered_df.groupby('order_id').apply(aggregate_results, include_groups=False).reset_index()
    return results[(results["profit_loss"] == "loss") | (results["profit_loss"] == "profit")]


if __name__ == '__main__':
    st.title('Bot 2 청산된 주문 분석')

    # 데이터 로드 및 전처리
    json_file_path = 'test.json'
    df = load_and_preprocess_data(json_file_path)

    user_list = df['user_id'].unique()
    selected_user = st.selectbox('유저 선택:', user_list)

    profit_or_lost_result = get_user_filtered_results(df, selected_user)
    # 인덱스를 1부터 시작하도록 조정
    profit_or_lost_result.index = np.arange(1, len(profit_or_lost_result) + 1)

    # 'order_id' 컬럼 제거
    profit_or_lost_result = profit_or_lost_result.drop(columns=['order_id'])
    print(profit_or_lost_result)

    # 이제 DataFrame을 Streamlit에 표시
    st.dataframe(profit_or_lost_result, use_container_width=True)

    st.dataframe(profit_or_lost_result, use_container_width=True)

    # 시간 범위 계산 및 표시는 사용자 선택에 따른 데이터로부터 수행
    start_timestamp = df['timestamp'].min()
    end_timestamp = df['timestamp'].max()
    st.write(f"{selected_user} 데이터 시간 범위: {start_timestamp} 부터 {end_timestamp} 까지")
