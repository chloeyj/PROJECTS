'''
Kiwoom.py
@author : yeojin

- Description : KIWOOM API를 이용하여 주가 데이터를 수집하는 파일
- Updated on : 2017.11.06

'''

import sys, time, pymysql
from PyQt4.QtGui import *  # QApplication 포함
import pandas as pd
from Kiwoom import Kiwoom  # Kiwoom 클래스
import datetime, math


def init():
    """ [init()함수] : 초기화 함수
        - QApplication 인스턴스를 전역 변수로 초기화
        - KIWOOM 인스턴스를 전역 변수로 초기화 및 로그인
        - Pymysql cursor 인스턴스를 전역 변수로 초기화
    """
    app = QApplication(sys.argv)  # QWidget 사용 전 QApplication 인스턴스 생성
    # Kiwoom 인스턴스 생성
    kiwoom = Kiwoom()
    # 2. 로그인
    kiwoom.login()

    # DB Connect
    conn = pymysql.connect(host='211.180.114.131', port=3306, user='user', passwd='!J12341234', db='financial_analysis',
                           charset='utf8')
    cur = conn.cursor()

    return app, kiwoom, cur


def get_code_list(market_code):
    """ [get_code_list()함수] : KIWOOM API의 GetCodeListByMarket() 함수를 사용하여 market_code에 따른 종목 코드 리스트를 반환하는 함수
        market_code : 시장 코드
    """

    stock_code_list = kiwoom.GetCodeListByMarket(market_code)  # 코스닥
    stock_code_name_dict = {}
    for code in stock_code_list:
        stock_code_name_dict[code] = kiwoom.GetMasterCodeName(code)

    return stock_code_list, stock_code_name_dict


def comm_get_data_min(stock_code, tick_type, item_name, tr_code, exist_or_not):
    """ [comm_get_data_min()함수] : KIWOOM API의 주식분봉차트조회요청 TR를 이용하여 특정 종목 코드의 분봉 주가 데이터를 수집하는 함수
        stock_code : 종목 코드
        TICK_TYPE : 틱 타입(1,3,5,10,30)
        item_name : SetInputValue()의 아이템명 (종목코드, 업종코드)
        tr_code : 트랜잭션 코드
    """
    # 1. 입력값 설정하기
    kiwoom.SetInputValue(item_name, stock_code)  # 종목코드
    kiwoom.SetInputValue("틱범위", tick_type)  # 1:1분, 3:3분, 5:5분, 10:10분, 15:15분, 30:30분, 45:45분, 60:60분
    kiwoom.SetInputValue("수정주가구분", 1)
    # 2. 데이터 받아올 변수 초기화
    kiwoom.InitOHLCVRawData()
    # 3. 조회요청 (처음 조회)
    kiwoom.CommRqData("주식분봉차트조회요청", tr_code, 0, "0101")  # -> OnReceiveTrData 이벤트 발생

    time.sleep(3)

    if exist_or_not == "0":

        while kiwoom.prev_next == '2':
            kiwoom.SetInputValue(item_name, stock_code)  # 종목코드
            kiwoom.SetInputValue("틱범위", tick_type)  # 1:1분, 3:3분, 5:5분, 10:10분, 15:15분, 30:30분, 45:45분, 60:60분
            kiwoom.SetInputValue("수정주가구분", 1)
            kiwoom.CommRqData("주식분봉차트조회요청", tr_code, 2, "0101")

            time.sleep(3)

    df = pd.DataFrame(kiwoom.ohlc, columns=['open', 'high', 'low', 'close', 'volume'], index=kiwoom.ohlc['date'])

    return df


def comm_get_data_day(stock_code, item_name, tr_code, exist_or_not):
    """ [comm_get_data_min()함수] : KIWOOM API의 주식일봉차트조회요청 TR를 이용하여 특정 종목 코드의 일봉 주가 데이터를 수집하는 함수
        stock_code : 종목 코드
        item_name : SetInputValue()의 아이템명 (종목코드, 업종코드)
        tr_code : 트랜잭션 코드
    """
    dt = datetime.datetime.now()
    today = str(dt.year) + str(dt.month) + str(dt.day)

    # 1. 입력값 설정하기
    kiwoom.SetInputValue(item_name, stock_code)  # 종목코드
    kiwoom.SetInputValue("기준일자", today)
    kiwoom.SetInputValue("수정주가구분", 1)
    # 2. 데이터 받아올 변수 초기화
    kiwoom.InitOHLCVRawData()
    # 3. 조회요청 (처음 조회)
    kiwoom.CommRqData("주식일봉차트조회요청", tr_code, 0, "0101")  # -> OnReceiveTrData 이벤트 발생

    time.sleep(2)

    if exist_or_not == "0":

        while kiwoom.prev_next == '2':
            kiwoom.SetInputValue(item_name, stock_code)  # 종목코드
            kiwoom.SetInputValue("기준일자", today)
            kiwoom.SetInputValue("수정주가구분", 1)
            kiwoom.CommRqData("주식일봉차트조회요청", tr_code, 2, "0101")

            time.sleep(2)

    df = pd.DataFrame(kiwoom.ohlc, columns=['open', 'high', 'low', 'close', 'volume'], index=kiwoom.ohlc['date'])

    return df


def data_transform(dataframe, tick_type):
    """ [comm_get_data_min()함수] : OHLCV 데이터를 저장한 KIWOOM 클래스의 OHLCV 인스턴스의 형태를 변환하는 함수
        dataframe : 기존 dataframe 형 인스턴스
        TICK_TYPE : 일봉, 분봉 구분("minute","day")
    """
    date_time = []

    df = dataframe
    df['date'] = df.index
    df = df.reset_index(drop=True)
    df = df.sort_index(ascending=False)
    df = df.reset_index(drop=True)

    for i in range(0, len(df)):
        if tick_type == "minute":
            regdate = datetime.datetime.strptime(df['date'][i][0:12], "%Y%m%d%H%M")
            date_time.append(regdate)
        elif tick_type == "day":
            regdate = datetime.datetime.strptime(df['date'][i][0:8], "%Y%m%d")
            date_time.append(regdate)
    df['date'] = date_time
    df['open'] = abs(df['open'])
    df['high'] = abs(df['high'])
    df['low'] = abs(df['low'])
    df['close'] = abs(df['close'])

    return df


def insert_into_db(dataframe, stock_code, stock_name, table_name):
    """ [insert_into_db()함수] : 특정 주가 데이터를 특정 table에 insert 하는 함수
        dataframe : date, open, high, low, close, volume 6개 칼럼을 갖고 있는 dataframe 형식의 데이터
        stock_code : 종목 코드
        stock_name : 종목 명
        table_name : DB 테이블 명
    """
    df = dataframe
    stock_code = stock_code
    stock_name = stock_name

    for i in df.index:

        date = df.ix[i]['date']
        open_value = df.ix[i]['open']
        high_value = df.ix[i]['high']
        low_value = df.ix[i]['low']
        close_value = df.ix[i]['close']
        volume = df.ix[i]['volume']

        if (stock_code == "101") | (stock_code == "001"):  # KOSPI INDEX , KOSDAQ INDEX
            try:
                cur.execute(
                    "insert into " + table_name + "(date, stock_name, open, high, low, close, volume) values('%s', '%s','%f','%f','%f','%f', '%d')" % (
                        date, stock_name, open_value, high_value, low_value, close_value, volume))
            except Exception as e:
                print(e)
        else:
            try:
                cur.execute(
                    "insert into " + table_name + "(date, stock_code, stock_name, open, high, low, close, volume) values('%s','%s', '%s','%f','%f','%f','%f', '%d')" % (
                    date, stock_code, stock_name, open_value, high_value, low_value, close_value, volume))
            except Exception as e:
                print(e)


def collect_price_data(code_type, tick_type, stock_code_list, stock_code_name_dict):
    """ [collect_price_data()함수] : 주가 데이터를 수집 및 형태 변형 후 DB에서 가장 마지막 데이터를 쿼리하여 이후 데이터를 DB에 INSERT 하는 함수
        code_type : 종목 타입 (kospi, kospi_index, kosdaq, kosdaq_index)
        tick_type : [tick_type1, tick_type2] (tick_type1 : "1", "30", "60" / tick_type2 : "day", "minute")
        stock_code_list : 리스트 형태의 종목 코드
        stock_code_name_dict : key 값이 종목 코드, value 값이 종목 명인 딕셔너리 형태의 변수
    """
    table_name = ""
    if (tick_type[1] == "minute"):
        table_name = code_type + "_" + tick_type[0] + tick_type[1] + "_value"
    elif (tick_type[1] == "day"):
        table_name = code_type + "_" + tick_type[1] + "_value"

    print("code type : " + code_type)
    print("number of code : " + str(len(stock_code_list)) + "\n")

    item_name = "종목코드"
    tr_code = "opt10081"  # 일봉
    if (code_type == "kospi_index") | (code_type == "kosdaq_index"):  # INDEX
        item_name = "업종코드"
        if (tick_type[1] == "day"):  # 일봉
            tr_code = "opt20006"
        else:  # 분봉
            tr_code = "opt20005"
    elif (tick_type[1] == "minute"):  # 분봉
        tr_code = "opt10080"

    for i in range(0, len(stock_code_list)):

        print(str(i) + ". " + str(stock_code_name_dict[stock_code_list[i]] + "( " + stock_code_list[i] + ")"))

        # specify where the data oc specific code is exist or not
        exist_or_not = "1"  # exist

        # 새로운 종목 구분
        if (code_type != "kospi_index") & (code_type != "kosdaq_index"):  # INDEX
            sql = "select stock_code from " + table_name + " where stock_code = '" + stock_code_list[i] + "'"
            if (cur.execute(sql) == 0):
                # data not exist
                exist_or_not = "0"

        if (tick_type[1] == "day"):
            df = comm_get_data_day(stock_code_list[i], item_name, tr_code, exist_or_not)
        else:
            df = comm_get_data_min(stock_code_list[i], tick_type[0], item_name, tr_code, exist_or_not)

        transformed_dataframe = data_transform(df, tick_type[1])

        # 레코드 데이터 있는 경우
        if len(transformed_dataframe) != 0:

            # 종목 출력
            # print(stock_code_list[i])

            # find date of last data in DB
            sql = "select date from " + table_name + " where stock_code = '" + stock_code_list[
                i] + "' order by date desc limit 1"

            if (code_type == "kospi_index") | (code_type == "kosdaq_index"):  # INDEX
                sql = "select date from " + table_name + " order by date desc limit 1"

            # 기존 데이터가 있는 경우
            if (cur.execute(sql) != 0):
                last_date = cur.fetchall()[0][0]

                # convert data type of "date" column of "transformed dataframe" variable
                date_series = transformed_dataframe["date"].dt.strftime("%Y-%m-%d %H:%M:%S")

                # find index of last date
                x = date_series.str.find(last_date)
                true_x = [i for i, x in enumerate(x) if x == 0]
                if len(true_x) != 0:
                    start_index = true_x[0] + 1
                else :
                    start_index = 0

                # slice dataframe
                transformed_dataframe = transformed_dataframe[start_index: ]

            # Insert into DB
            insert_into_db(transformed_dataframe, stock_code_list[i], stock_code_name_dict[stock_code_list[i]],
                           table_name)


def main():
    """ [main()함수] : 메인
        - kospi, kosdaq, kospi_index, kosdaq_index 네 종목 타입에 속하는 종목의 일봉, 30분봉, 60분봉
        - 주가를 수집하여 DB에 저장하는 함수
    """
    global app, kiwoom, cur
    app, kiwoom, cur = init()

    # KOSPI
    start = time.time()
    stock_code_list, stock_code_name_dict = get_code_list(0)
    collect_price_data("kospi", ["1", "day"], stock_code_list, stock_code_name_dict)
    collect_price_data("kospi", ["30", "minute"], stock_code_list, stock_code_name_dict)
    collect_price_data("kospi", ["60", "minute"], stock_code_list, stock_code_name_dict)
    end = time.time()
    running_time = end - start
    m, s = divmod(running_time, 60)
    h, m = divmod(m, 60)
    print("KOSPI running time : " + str(math.floor(h)) + " hours " + str(math.floor(m)) + " minutes " + str(
        math.floor(s)) + " seconds")

    # KOSDAQ
    start = time.time()
    stock_code_list, stock_code_name_dict = get_code_list(10)
    collect_price_data("kosdaq", ["1", "day"], stock_code_list, stock_code_name_dict)
    collect_price_data("kosdaq", ["30", "minute"], stock_code_list, stock_code_name_dict)
    collect_price_data("kosdaq", ["60", "minute"], stock_code_list, stock_code_name_dict)
    end = time.time()
    running_time = end - start
    m, s = divmod(running_time, 60)
    h, m = divmod(m, 60)
    print("KOSDAQ running time : " + str(math.floor(h)) + " hours " + str(math.floor(m)) + " minutes " + str(
        math.floor(s)) + " seconds")

    # KOSPI INDEX
    start = time.time()
    collect_price_data("kospi_index", ["1", "day"], ["001"], {"001": "KOSPI"})
    collect_price_data("kospi_index", ["30", "minute"], ["001"], {"001": "KOSPI"})
    collect_price_data("kospi_index", ["60", "minute"], ["001"], {"001": "KOSPI"})
    end = time.time()
    running_time = end - start
    m, s = divmod(running_time, 60)
    h, m = divmod(m, 60)
    print("KOSPI INDEX running time : " + str(math.floor(h)) + " hours " + str(math.floor(m)) + " minutes " + str(
        math.floor(s)) + " seconds")

    # KOSDAQ INDEX
    start = time.time()
    collect_price_data("kosdaq_index", ["1", "day"], ["101"], {"101": "KOSDAQ"})
    collect_price_data("kosdaq_index", ["30", "minute"], ["101"], {"101": "KOSDAQ"})
    collect_price_data("kosdaq_index", ["60", "minute"], ["101"], {"101": "KOSDAQ"})
    end = time.time()
    running_time = end - start
    m, s = divmod(running_time, 60)
    h, m = divmod(m, 60)
    print("KOSDAQ INDEX running time : " + str(math.floor(h)) + " hours " + str(math.floor(m)) + " minutes " + str(
        math.floor(s)) + " seconds")

    return


main()