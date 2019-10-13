from price_data_crawling import *

# --- 데이터 조회 및 DB 저장 --- #
def main():

    # 변수 초기화
    init()

    # 삼성전자 일봉 데이터 조회 및 DB 저장
    stock_code_list = ["005930"]
    stock_code_name_dict = {"005930" : "삼성전자"}

    day_data = collect_price_data("kospi", ["1", "day"], stock_code_list, stock_code_name_dict)
    print(day_data.head())

    '''
    KOSPI
    
    - KOSPI 종목 내 모든 종목 코드 및 코드명 조회
    - 모든 종목 데이터 조회 및 DB 저장 
    - 일봉, 30분봉, 60분봉, 월봉
    '''

    # # KOSPI 내 모든 종목 코드 및 코드명 조회
    # stock_code_list, stock_code_name_dict = get_code_list(0) # market_code : 0 (KOSPI)
    #
    # # 데이터 조회 및 DB 저장
    # collect_price_data("kospi", ["1", "day"], stock_code_list, stock_code_name_dict) # 일봉
    # collect_price_data("kospi", ["30", "minute"], stock_code_list, stock_code_name_dict) # 30분봉
    # collect_price_data("kospi", ["60", "minute"], stock_code_list, stock_code_name_dict) # 60분봉
    # collect_price_data("kospi", ["1", "month"], stock_code_list, stock_code_name_dict) # 월봉

    '''
    KOSDAQ

    - KOSDAQ 종목 내 모든 종목 코드 및 코드명 조회
    - 모든 종목 데이터 조회 및 DB 저장 
    - 일봉, 30분봉, 60분봉, 월봉
    '''

    # # KOSDAQ 내 모든 종목 코드 및 코드명 조회
    # stock_code_list, stock_code_name_dict = get_code_list(10) # market_code : 10 (KOSDAQ)
    #
    # # 데이터 조회 및 DB 저장
    # collect_price_data("kosdaq", ["1", "day"], stock_code_list, stock_code_name_dict) # 일봉
    # collect_price_data("kosdaq", ["30", "minute"], stock_code_list, stock_code_name_dict) # 30분봉
    # collect_price_data("kosdaq", ["60", "minute"], stock_code_list, stock_code_name_dict) # 60분봉
    # collect_price_data("kosdaq", ["1", "month"], stock_code_list, stock_code_name_dict) # 월봉

# --- 매수 및 매도 --- #
def main2(account, account_pwd): # account : 계좌 번호, account_pwd : 계좌 비밀 번호

    # 변수 초기화
    app, kiwoom, cur = init()

    '''
    매수
    '''
    stock_code = "002350" # 종목 코드
    amount = 10 # 주문 수량

    # 주문 체결 (시장가로 매수)
    kiwoom.SendOrder("주식주문",  # 사용자 구분 요청 명
                           "0101",  # 화면 번호
                           account,  # 계좌 번호
                           1,  # 주문 유형 - 1 : 신규 매수
                           stock_code,  # 종목 코드
                           amount,  # 주문 수량
                           "",  # 주문가격 - 시장가일 경우 공백
                           "03",  # 호가구분 - 03 : 시장가
                           "")  # 원주문번호 - 신규매수일 경우 공백

    # 잔고 내역 요청
    kiwoom.SetInputValue("계좌번호", account)
    kiwoom.SetInputValue("비밀번호", account_pwd)
    kiwoom.SetInputValue("조회구분", "2")  # 개별 조회
    kiwoom.CommRqData("계좌평가잔고내역요청", "opw00018", 0, "2000")

    # 주문 체결 (지정가로 매수)
    # kiwoom.SendOrder("주식주문",  # 사용자 구분 요청 명
    #                  "0101",  # 화면 번호
    #                  account,  # 계좌 번호
    #                  1,  # 주문 유형 - 1 : 신규 매수
    #                  stock_code,  # 종목 코드
    #                  amount,  # 주문 수량
    #                  "",  # 주문가격 - 지정가일 경우 가격 설정
    #                  "01",  # 호가구분 - 01 : 지정가
    #                  "")  # 원주문번호 - 신규매수일 경우 공백

    '''
    매도
    '''
    stock_code = "002350"  # 종목 코드
    amount = 5  # 주문 수량

    # 주문 체결
    res = kiwoom.SendOrder("주식주문",  # 사용자 구분 요청 명
                           "0101",  # 화면 번호
                           account,  # 계좌 번호
                           2,  # 주문 유형 - 2 : 신규 매도
                           stock_code,  # 종목 코드
                           amount,  # 주문 수량
                           "",  # 주문가격 - 시장가일 경우 공백
                           "03",  # 호가구분 - 03 : 시장가
                           "")  # 원주문번호 - 신규매수일 경우 공백

    # 잔고 내역 요청
    kiwoom.SetInputValue("계좌번호", account)
    kiwoom.SetInputValue("비밀번호", account_pwd)
    kiwoom.SetInputValue("조회구분", "2")  # 개별 조회
    kiwoom.CommRqData("계좌평가잔고내역요청", "opw00018", 0, "2000")