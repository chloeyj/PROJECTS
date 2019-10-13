import pymysql
from celery import shared_task
from celery_progress.backend import ProgressRecorder
import time

'''
노이즈 단어 정의
'''
noise_keywords = ["입장", "입장에서", "경험을", "표준", "구조", "경험", "대표이사",
                  "본인", "자신", "관계자", "중에", "본사", "자사", "배송기사", "채팅캣", "업무",
                  "제품", "마케팅", "그룹", "회사", "사용자", "육성", "교수팀", "고문", "기술로드맵",
                  "지적재산권", "정보보안단단장", "이외", "이메일이지만", "외부개발자", "애플리케이션",
                  "대학", "영입하", "교육", "이미지", "등장", "소개", "매출", "분야", "일본",
                  "성장", "투자정보", "네트워크", "환경", "계정", "기술", "소프트웨어",
                  "원가", "재고", "구매", "자산", "생산", "파일", "정보", "차원", "서버", "친밀", "친밀도",
                  "사업자", "검사", "범죄자들", "제공하", "선정담당", "고객", "소유", "활용도",
                  "차원", "데이터", "문서", "드론자격증", "대한무인항공서비스", "대표이사", "커뮤니케이션"]

'''
DB에 연결한 후 CURSOR를 반환하는 함수
'''
def connect_db():

    conn = pymysql.connect(host="211.180.114.131", user="user", password="!J12341234", db="company_search",
                           charset="utf8")

    cursor = conn.cursor()

    return cursor

def select_company_db():

    cursor = connect_db()

    sql = "select idx, type, company_name from company_db where filter = '0'"

    try :
        cursor.execute(sql)
    except Exception as e:
        print(e)

    rows = cursor.fetchall()

    conn.close()

    return rows

def delete_company(company):
    cursor = connect_db()

    sql = "delete from company_db where company_name = '" + company + "'"

    try:
        cursor.execute(sql)
    except Exception as e:
        print(e)

    conn.close()

def insert_company(company, type):

    cursor = connect_db()

    sql = "insert into company_db (type, company_name) values ('{}', '{}')".format(type, company)

    try:
        cursor.execute(sql)
    except Exception as e:
        print(e)

    conn.close()


def update_company(before, after):

    cursor = connect_db()

    sql = "update company_db set company_name = '{}' where company_name = '{}'".format(after, before)

    try:
        cursor.execute(sql)
    except Exception as e:
        print(e)

    conn.close()