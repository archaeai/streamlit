import streamlit as st
import pandas as pd
import numpy as np
from st_aggrid import GridOptionsBuilder, AgGrid


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
        'entry_time': group['timestamp'].iloc[0],
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
    filtered_df = filtered_df.sort_values(by='timestamp', ascending=True)
    start_time = filtered_df['timestamp'].min()
    end_time = filtered_df['timestamp'].max()
    results = filtered_df.groupby('order_id').apply(aggregate_results, include_groups=False).reset_index()
    pnl = results[(results["profit_loss"] == "loss") | (results["profit_loss"] == "profit")]
    pnl_sorted = pnl.sort_values('entry_time', ascending=True)
    return pnl_sorted, filtered_df, start_time, end_time


def get_winrate(_df):
    _total_num = len(_df)
    _win_count = _df['profit_loss'].value_counts().get("profit", 0)
    _win_rate = round((_win_count / _total_num * 100), 2) if _total_num >0 else 0

    # df 대신 _df 사용
    _split_water_open_sum = _df.get('split_open_water', pd.Series([0])).sum()
    _split_water_close_sum = _df.get('split_close_water', pd.Series([0])).sum()

    _split_bull_open_sum = _df.get('split_open_bull', pd.Series([0])).sum()
    _split_bull_close_sum = _df.get('split_close_bull', pd.Series([0])).sum()

    if _split_water_open_sum > 0:
        _split_water_win_rate = round((_split_water_close_sum / _split_water_open_sum * 100), 2)
    else:
        _split_water_open_sum = 0
        _split_water_win_rate = 0

    if _split_bull_open_sum > 0:
        _split_bull_win_rate = round((_split_bull_close_sum / _split_bull_open_sum * 100), 2)
    else:
        _split_bull_open_sum = 0
        _split_bull_win_rate = 0

    return (_win_rate, _split_water_win_rate, _split_bull_win_rate, _total_num, _win_count, _split_water_open_sum,
            _split_water_close_sum, _split_bull_open_sum, _split_bull_close_sum)


if __name__ == '__main__':
    st.title('Bot 2 청산된 주문 분석')
    # Initialize connection.
    conn = st.connection('mysql', type='sql')
    # Perform query. 캐쉬 10분 설정 로직.
    df = conn.query('SELECT * from trade_logs;', ttl=600)

    # 유저 리스트 가져오기
    user_list = df['user_id'].unique()
    selected_user = st.selectbox('유저 선택:', user_list)

    st.write(f" order id 옆에 체크박스를 클릭하면, 세부 정보를 볼 수 있습니다.")

    # dateframe 가져오기
    profit_or_lost_result, filtered_by_user, start_timestamp, end_timestamp = get_user_filtered_results(df,
                                                                                                        selected_user)

    # 승률 보기
    (win_rate, split_water_win_rate, split_bull_win_rate, total_num, win_count, split_water_open_sum,
     split_water_close_sum, split_bull_open_sum, split_bull_close_sum) = get_winrate(profit_or_lost_result)
    st.write(f"💲청산 주문 : {total_num} 😊익절 주문 : {win_count} 😅손절 주문 : {total_num - win_count} ")
    st.write(f"💧물타기 주문 : {split_water_open_sum} 💧물타기 익절 : {split_water_close_sum} ")
    st.write(f"🔥불타기 주문 : {split_bull_open_sum} 🔥불타기 익절 : {split_bull_close_sum} ")
    st.write(f"📢 승률 : {win_rate}%, 💧물타기 승률 : {split_water_win_rate}% "
             f", 🔥불타기 승률 : {split_bull_win_rate} ")

    # AgGrid 설정에 include_columns 사용
    gb = GridOptionsBuilder.from_dataframe(profit_or_lost_result)
    gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_selection('single', use_checkbox=True)
    gridOptions = gb.build()

    # AgGrid 테이블 표시
    response = AgGrid(

        profit_or_lost_result,
        gridOptions=gridOptions,
        fit_columns_on_grid_load=False,
        height=400,
        width='100%',
        enable_enterprise_modules=True
    )

    selected = response['selected_rows']

    if selected:
        selected_order_ids = [row['order_id'] for row in selected]
        selected_orders = filtered_by_user[filtered_by_user['order_id'].isin(selected_order_ids)]
        st.write(selected_orders)
