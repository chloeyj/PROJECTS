import numpy as np

def trading_by_trend(new_df):
    new_df = new_df

    index = 0  # 0-> 매도 상태, 1-> 매수 상태

    price = 0
    return_list = []
    buy_date_list = []
    sell_date_list = []
    trading_signal = []
    buy_price_list = []
    sell_price_list = []

    # 기본 사고 팔기 +++++++++++++++++++++++++++++++++++++++++++++++++++++

    first_buy_price = new_df['open'][0]
    sell_price = new_df['open'][len(new_df) - 1]
    buy_hold_return = (sell_price - first_buy_price) / first_buy_price * 100


    for j in range(0, len(new_df)):
        # 매도 상태일 때
        if index == 0:
            # 다음날 주가의 움직임이 '상승'일 때
            if new_df['pred'][j] == 1:
                if j + 1 != len(new_df):
    #                     trading_signal.append('Buy')
                    price = new_df['open'][j + 1]
                    buy_price_list.append(price)
                    buy_date_list.append(new_df['date'][j + 1])
                    index = 1
                else:
                    trading_signal.append('')
            else:
                trading_signal.append('')
        elif index == 1:
            if new_df['pred'][j] == 0:
                if j + 1 == len(new_df):
                    print(new_df['date'][j])
                    print(new_df['open'][j])
                else:
                    trading_signal.append('Sell')
                    return_list.append((new_df['open'][j + 1] - price) / price * 100)
                    sell_date_list.append(new_df['date'][j + 1])
                    sell_price_list.append(new_df['open'][j + 1])
                    index = 0
            else:
                trading_signal.append('')
                if (j + 1 == len(new_df)):
                    sell_price = new_df['open'][j]
                    sell_date_list.append(new_df['date'][j])
                    sell_price_list.append(new_df['open'][j])
                    return_list.append((sell_price - price) / price * 100)

    profit = np.cumsum(return_list)[-1]
    return buy_date_list, buy_price_list, sell_date_list, sell_price_list, return_list, profit, buy_hold_return

def add_row(df, row):
    df.loc[-1] = row
    df.index = df.index + 1
    return df.sort_index()
