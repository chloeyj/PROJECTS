import json
from django.shortcuts import render, HttpResponse, HttpResponseRedirect
from app.main_query_test6 import main as main_query_master
from app.module import get_derived_query
from app.utils import select_company_db, delete_company, insert_company, update_company, my_task
from celery.result import AsyncResult
from mysite.celery import app
from django.contrib.auth.decorators import login_required

# Create your views here.


'''
메인 검색 페이지 렌더링 함수
- 로그인 되었을 때만 접속 가능
'''
@login_required(login_url='/accounts/login/')
def main(request):

    return render(request, "index.html")

'''
기업 DB 페이지 렌더링 함수
- 로그인 되었을 때만 접속 가능
'''
@login_required(login_url='/accounts/login/')
def db(request):

    return render(request, "db.html")


'''
기업 검색 프로세스를 동작시키는 함수 (CELERY 연동)
'''
def search(request):

    if request.user.is_anonymous: return HttpResponseRedirect("/accounts/login/")

    user = request.user.username

    html_select = request.GET.get("html_select", None)
    pdf_select = request.GET.get("pdf_select", "")
    keyword_list = request.GET.get("keyword_list", None)
    related_keyword_list = request.GET.get("related_keyword_list", None)
    required_keyword_list = request.GET.get("required_keyword_list", None)
    except_keyword_list = request.GET.get("except_keyword_list", None)

    docType1 = True if html_select == "1" else False
    docType2 = True if pdf_select == "1" else False

    keyword_list = [item.strip() for item in keyword_list.split(",")]
    related_keyword_list = [item.strip() for item in related_keyword_list.split(",")]
    required_keyword_list = [item.strip() for item in required_keyword_list.split(",")]
    except_keyword_list = [item.strip() for item in except_keyword_list.split(",")]

    print("검색 키워드", keyword_list)
    print("관련 키워드", related_keyword_list)
    print("필수 포함 키워드", required_keyword_list)
    print("필수 제외 키워드", except_keyword_list)
    print("HTML 사용 여부", docType1)
    print("PDF 사용 여부", docType2)

    async_result = ""
    if keyword_list != []:
        async_result = main_query_master.delay(keyword_list, related_keyword_list, required_keyword_list, except_keyword_list, [docType1, docType2])

    return HttpResponse(json.dumps(async_result.id), content_type="application/json")

'''
유사어(동의어) 검색 결과를 반환하는 함수
'''
def get_derived_query_list(request):

    keyword = request.GET.get("keyword", None)

    query_list = get_derived_query(keyword)

    return HttpResponse(json.dumps(query_list, ensure_ascii=False), content_type="application/json")


'''
검색 프로세스 중단 함수 (CELERY 연동)
'''
def stop_task(request):

    task_id = request.GET.get("task_id", None)

    print("i will revoke ", task_id)

    app.control.revoke(task_id, terminate=True)

    return HttpResponse("", content_type="application/json")


'''
기업 DB 내 모든 기업 데이터 조회 후 반환하는 함수
'''
def select_db(request):

    res = select_company_db()

    return HttpResponse(json.dumps(res, ensure_ascii=False), content_type="application/json")

'''
기업 DB 내 특정 기업명의 데이터를 삭제하고 전체 기업 데이터를 반환하는 함수
'''
def delete_db(request):

    company = request.GET.get("company", None)

    delete_company(company)

    res = select_company_db()

    return HttpResponse(json.dumps(res, ensure_ascii=False), content_type="application/json")


'''
기업 DB 내 새로운 기업 데이터를 추가하고 전체 기업 데이터를 반환하는 함수
'''
def insert_db(request):

    company = request.GET.get("company", None)
    type = request.GET.get("type", None)

    print(company, type)

    insert_company(company, type)

    res = select_company_db()

    return HttpResponse(json.dumps(res, ensure_ascii=False), content_type="application/json")

'''
기업 DB 내 특정 기업의 데이터를 업데이트하고 전체 기업 데이터를 반환하는 함수
'''
def update_db(request):

    before = request.GET.get("before", None)
    after = request.GET.get("after", None)

    print(before, after)

    update_company(before, after)

    res = select_company_db()

    return HttpResponse(json.dumps(res, ensure_ascii=False), content_type="application/json")

'''
기업 검색 결과를 반환하는 함수 (CELERY 연동)
'''
def get_task_result(request):

    task_id = request.GET.get("task_id")

    res = AsyncResult(task_id)

    data = res.get()

    return HttpResponse(json.dumps(data), content_type = "application/json")

def get_sample_result(request):

    data = {"퓨처웨어(주)" :
                {"count" : 5, "db_exist" : 0, "paragraph_list" : ["","","","",""], "case_list" : [1, 0, 0, 0, 0], "title_list" : ["a_case1","b_case0","c_case0","d_case0","e_case0"], "url_list" : ["http://www.naver.com", "http://www.naver.com", "http://www.naver.com", "http://www.naver.com", "http://www.naver.com"], "company_type" : "중소기업, 주식회사", "business_type" : "응용 소프트웨어 개발 및 공급업", "website_url" : "http://www.naver.com", "contact_number" : "02-0000-0000"},
            "(주)컴팩트디" :
                {"count" : 4, "db_exist" : 0, "paragraph_list" : ["","","",""], "case_list" : [1, 0, 1, 0], "title_list" : ["a_case1","b_case0","c_case1","d_case0"], "url_list" : ["http://daum.net", "http://daum.net", "http://daum.net", "http://daum.net"], "company_type": "-", "business_type": "-", "website_url": "-", "contact_number": "-"}}

    data2 = {
    "(주)미트뱅크" :
        {"count" : 3, "db_exist" : 0, "paragraph_list" : ["","",""], "title_list" : ["a_case1","b_case0","c_case1"], "case_list" : [1, 0, 1], "url_list" : ["http://www.naver.com", "http://www.naver.com", "http://www.naver.com"], "company_type": "중소기업, 외부감사법인, 수출입 기업", "business_type": "육류 포장육 및 냉동육 가공업(가금류 제외)", "website_url": "http://www.naver.com", "contact_number": "02-0000-0000"},
    "(주)예담엔지니어링" :
        {"count" : 2, "db_exist" : 0, "paragraph_list" : ["",""], "title_list" : ["a_case1","b_case0"], "case_list" : [1, 0], "url_list" : ["http://www.naver.com", "http://www.naver.com"], "company_type": "중소기업, 주식회사", "business_type": "기타 엔지니어링 서비스업", "website_url": "http://www.naver.com", "contact_number": "02-0000-0000"},
    "건영포장(주)" :
        {"count" : 1, "db_exist" : 0, "paragraph_list" : [""], "title_list" : ["a_case1"], "case_list" : [1], "url_list" : ["http://www.naver.com"], "company_type": "중소기업, 주식회사", "business_type": "목재 포장용 상자, 드럼 및 유사용기 제조업", "website_url": "http://www.naver.com", "contact_number": "02-0000-0000"}}


    all_data = [data, data2]

    return HttpResponse(json.dumps(all_data), content_type = "application/json")