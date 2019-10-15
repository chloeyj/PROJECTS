import pandas as pd
import tensorflow as tf
import datetime
import matplotlib.pyplot as plt
from q_learning_agent import Agent
from utils import trading_by_trend

# Hyperparameters
initial_money = 10000000
window_size = 30
skip = 1
batch_size = 32

# Selected highly correlated features
relevant_features = ["close", "high", "low", "open", "upperband", "middleband", "lowerband",
                     "dema", "ema", "ht_trendline", "kama", "ma", "mama", "fama",
                     "midpoint", "midprice", "sar", "sma", "t3", "tema", "trima",
                     "wma", "plus_dm", "obv", "avgprice", "medprice", "typprice", "wclprice", "atr"]

feature_num = len(relevant_features)
state_size = window_size * feature_num

def main():

    model_name = "q_learning"

    # import data
    df = pd.read_csv('dataset/Samsung.csv')

    # split dataset
    temp = df.date.apply(lambda x: datetime.datetime.strptime(x, "%Y-%m-%d %H:%M:%S")).apply(lambda x: x.date() > datetime.date(2000, 1, 1))
    start_idx = temp[temp == True].argmin()
    df = df.iloc[start_idx:, :]  # 2000 ~
    df.reset_index(inplace=True, drop=True)

    test_start = datetime.datetime.strptime(df['date'].iloc[-1], "%Y-%m-%d %H:%M:%S").date() - pd.DateOffset(years=1) # last 1 year
    test_start_idx = df[df.date == test_start.strftime("%Y-%m-%d 00:00:00")].index[0]

    train_df = df.iloc[:test_start_idx, :]
    train_df.reset_index(inplace=True, drop=True)
    test_df = df.iloc[test_start_idx:, :]
    test_df.reset_index(inplace=True, drop=True)

    '''
    train model
    '''

    train_df = train_df.loc[:, relevant_features]
    test_df = test_df.loc[:, relevant_features]


    if 'Unnnamed: 0' in train_df.columns: del train_df['Unnamed: 0']
    if 'date' in train_df.columns: del train_df['date']

    # initialize agent
    trend = train_df.values.tolist()
    agent = Agent(state_size=state_size, window_size=window_size, trend=trend, skip=skip, batch_size=batch_size)

    print("Start Training...")
    agent.train(iterations=200, checkpoint=1, initial_money=initial_money)

    # save model
    saver = tf.train.Saver()
    saver.save(agent.sess, 'rl_model/{name}.ckpt'.format(name=model_name))
    agent.sess.close()

    # get test data

    if 'Unnamed: 0' in test_df.columns: del test_df['Unnamed: 0']
    if 'date' in test_df.columns: del test_df['date']

    '''
    test
    '''

    # initialize agent
    trend = test_df.values.tolist()
    agent = Agent(state_size=state_size,window_size=window_size,trend=trend,skip=skip,batch_size=batch_size)
    close = test_df.close

    # load model
    saver = tf.train.Saver()
    sess = tf.InteractiveSession()
    saver.restore(sess, 'rl_model/{name}.ckpt'.format(name=model_name))
    agent._set_session(sess)

    # predict
    states_buy, states_sell, total_gains, invest = agent.buy(initial_money=initial_money, close=close)
    agent.sess.close()

    if (len(states_buy) == 0 | (len(states_sell)) == 0) : return

    '''
    backtesting
    '''

    test_df = df.iloc[test_start_idx:, :]
    test_df.reset_index(inplace=True, drop=True)
    test_df = test_df[['date', 'close', 'high', 'low', 'open', 'volume']]

    test_df.loc[:, "pred"] = 2
    test_df.loc[states_buy, "pred"] = 1
    test_df.loc[states_sell, "pred"] = 0

    buy_date_list, buy_price_list, sell_date_list, sell_price_list, return_list, profit, buy_hold_return = trading_by_trend(
        test_df.copy())

    print("profit :", profit)
    print("buy_hold_return :", buy_hold_return)

    # make figure and save it

    buy_idx_list = [test_df[test_df.date == date].index[0] for date in buy_date_list]
    sell_idx_list = [test_df[test_df.date == date].index[0] for date in sell_date_list]

    fig = plt.figure(figsize=(15, 5))
    plt.plot(close, color='r', lw=2.)
    plt.plot(close, '^', markersize=10, color='m', label='buying signal', markevery=buy_idx_list)
    plt.plot(close, 'v', markersize=10, color='k', label='selling signal', markevery=sell_idx_list)
    plt.title('total gains %f, total investment %f%%' % (profit * initial_money, profit))
    plt.legend()
    fig = plt.gcf()

    fname = "figures/backtesting_result_with_" + model_name + ".png"
    fig.savefig(fname, bbox_inches='tight')
    plt.close()

if __name__ == '__main__':

    main()