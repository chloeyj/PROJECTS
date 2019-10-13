import pandas as pd
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
import requests as rs
import numpy as np
from konlpy.tag import Hannanum
from google.cloud import translate
import os, re, copy
from nltk.corpus import wordnet
from konlpy.tag import Kkma
from celery import shared_task
from celery_progress.backend import ProgressRecorder
from app.utils import select_company_db
from billiard.exceptions import Terminated
from bs4.element import Comment
import pymysql, urllib, cgi
from io import StringIO
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.psparser import PSEOF


'''
각종 변수 및 정규식 초기화 함수
'''
def init_variables(keyword_list, related_keyword_list):
    """ Initialize global variables """
    # print("1. init variables")

    global file_check, tagger, tempre, tempre2, tempre3, headers, patterns1, patterns2, augmented_keyword_list

    # downloadable file string pattern
    file_check = ["download", "down", "file", "pdf", "excel", "xlsx", "docx", "hwp", "youtube", "movie.daum.net", "wikipedia"]

    # Kkma tagger
    tagger = Hannanum()

    # request headers
    headers = {
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'en-US,en;q=0.8',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
    }


    '''
    \s - whitespace 문자와 매치, [ \t\n\r\f\v]와 동일한 표현식
    \S - whitespace 문자가 아닌 것과 매치, [^ \t\n\r\f\v]와 동일한 표현식
    \w - 문자 + 숫자와 매치, [a-zA-Z0-9]와 동일
    \W - 문자 + 숫자가 아닌 문자와 매치, [^a-zA-Z0-9]와 동일
    '''


    # regex pattern
    tempre = re.compile(r'[\w_]+') # (문자 and 숫자)
    tempre2 = re.compile(r'[\W_]+') # except (문자 or 숫자)
    tempre3 = re.compile("(\s+)") # any white space

    company_alias = ["회사", "기업", "브랜드", "브랜드명", "업체", "개발사", "제조사", "제작사", "제약사", "스타트업", "고객사", "게임사", "산업체"]

    subject_postpositions1 = ["에서", "사가", "사는", "과의",  "사에서", "에서는"]
    subject_postpositions2 = ["은", "는", "이", "가", "와", "도", "를"]

    patterns1 = [r'(%s){1}인{0,1} ㈜{0,1}([ㄱ-ㅣ가-힣()a-zA-Z0-9.%%\-\'"‘’社]+)에서{1}는{0,1} ' % '|'.join(company_alias),
                r'(%s){1}인{0,1} ㈜{0,1}([ㄱ-ㅣ가-힣()a-zA-Z0-9.%%\-\'"‘’社]+)[은는가와과도의을를,]{1} ' % '|'.join(company_alias),
                r' ([㈜ㄱ-ㅣ가-힣()a-zA-Z0-9.%%\-\'"‘’社]+)[이가] (개발한|출시한) ',
                r' ([㈜ㄱ-ㅣ가-힣()a-zA-Z0-9.%%\-\'"‘’社]+)의 기술은 ',
                r' ([㈜ㄱ-ㅣ가-힣()a-zA-Z0-9.%%\-\'"‘’社]+)와 같은 기업들{0,1}은 ',
                r'(([㈜ㄱ-ㅣ가-힣()a-zA-Z0-9.%%\-\'"‘’社]+[,|·] {0,1})*[㈜ㄱ-ㅣ가-힣()a-zA-Z0-9.%%\-\'"‘’社]+) 등 .{0,10}(%s){1}' % '|'.join(company_alias), # 김동 추가
                r'(%s){1}인{0,1} ([㈜ㄱ-ㅣ가-힣()a-zA-Z0-9.%%\-\'"‘’社]+)에 따르면'  % '|'.join(company_alias),
                r'(%s){1}인{0,1} [\'‘]([ㄱ-ㅣ가-힣()a-zA-Z0-9.%%\-社 ]+)[\'’][은는가와과도의,]{1} ' % '|'.join(company_alias),
                 ]

    patterns2 = [r'(\(주\)|\(주\) |㈜|㈜ )([ㄱ-ㅣ가-힣a-zA-Z.]+)(%s)[\W_]' % '|'.join(subject_postpositions1),
                r'(\(주\)|\(주\) |㈜|㈜ )([ㄱ-ㅣ가-힣a-zA-Z.]+)[%s][\W_]' % '|'.join(subject_postpositions2),
                r'(\(주\)|\(주\) |㈜|㈜ )([ㄱ-ㅣ가-힣a-zA-Z.]+)[\W_]',
                r'주식회사 ([ㄱ-ㅣ가-힣a-zA-Z.]+)[\W_]']

    '''
    figures = ".|-|•|※|▪|*|○|□|◈|․|❍"
    circled_number_indexer = "①|②|③|④|⑤|⑥|⑦|⑧|⑨"
    arabic_number_indexer = "Ⅰ|Ⅱ|Ⅲ|Ⅳ|Ⅴ|I|V"
    '''
    figures = ".|\uf0b7|\-|•|\u2022|※|\u203B|▪|\u25AA|*|○|\u25CB|□|\u25A1|◈|\u25C8|․|\u2024|❍|\u274D"
    korean_indexer = "가|나|다|라|마|바|사|아|자|차|카|타|파|하"
    circled_number_indexer = "①|\u2460|②|\u2461|③|\u2462|④|\u2463|⑤|\u2464|⑥|\u2465|⑦|\u2466|⑧|\u2467|⑨|\u2468"
    bracket_number_indexer = "1)|2)|3)|4)|5)|6)|7)|8)|9)|10)"
    arabic_number_indexer = "Ⅰ|\u2160|Ⅱ|\u2161|Ⅲ|\u2162|Ⅳ|\u2163|Ⅴ|"
    brackets = "\[|\]"
    sc_seperators = "|".join([figures, circled_number_indexer,
                              arabic_number_indexer, brackets])

    augmented_keyword_list = augment_keyword_alternatives(keyword_list, related_keyword_list)

    # initialize company list
    company_list = init_company_list()

    # initialize pymysql cursor
    cursor = connect_db()

    return tempre, tempre2, tempre3, subject_postpositions1, subject_postpositions2, patterns1, patterns2, augmented_keyword_list, company_list, cursor, sc_seperators

'''
검색 결과 DICTIONARY 변수 초기화 및 반환 함수
'''
def init_count_dict():

    # company_count_dict : HTML, company_count_dict2 : PDF
    global company_count_dict, company_count_dict2
    company_count_dict, company_count_dict2 = {}, {}

    return company_count_dict, company_count_dict2

'''
기업 DB 내 기업명 조회 및 반환 함수
'''
def init_company_list():
    """ Initialize company list variable """

    rows = select_company_db()

    company_list = []

    for row in rows:
        if row[2] != None:
            company_list.append(row[2].lower().strip())

    return list(np.unique(company_list))

'''
GOOGLE CUSTOM SEARCH API SERVICE 초기화 함수
'''
def getService():
    """ Build an Google Custom Search API service """
    service = build("customsearch", "v1", developerKey="AIzaSyCNLAU_Lunh5aJIo17DlslQvKoQGU7yDjA")

    return service

'''
유사어(유의어) 검색 및 반환 함수
'''
def get_derived_query(keyword):

    # google translate API
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "My Project-a8e42c74ea7e.json"
    translate_client = translate.Client()

    # Hannanum pos tagger
    hannanum = Hannanum()
    """ Retrieve derived queries from keyword by using WordNet Synset """
    nouns = [word for word, pos in hannanum.pos(keyword) if pos == "N"]
    syn_dict = {}
    query_list = []

    for noun in nouns:
        result = translate_client.translate(noun, target_language="en")
        if len(result["translatedText"].split(" ")) > 1:  # 복합 명사 처리 안함
            continue
        else:
            translated_noun = result["translatedText"]
            # print(noun, translated_noun)
            for syn in wordnet.synsets(translated_noun):
                synonyms = []
                if syn.pos() == "n":
                    syn_word = syn.name().split(".")[0]
                    synonyms.append(syn_word)

        syn_dict[noun] = synonyms

    if len(syn_dict) > 0:
        for noun in syn_dict:
            for syn in syn_dict[noun]:
                syn_ko = translate_client.translate(syn, target_language="ko")["translatedText"]
                query_list.append(keyword.replace(noun, syn_ko))

    return list(np.unique(query_list))

'''
GOOGLE CUSTOM SEARCH API 기반 검색 결과 URL 추출 함수
'''
def google_search(keyword_list, except_keyword_list, required_keyword_list):
    """ Search urls relevant with keyword by using Google Custom Search API """
    service = getService()  # GOOGLE API 연결

    response_url = []  # URL list

    query_list = keyword_list

    print("query_list", query_list)

    # print("2. retrieve related urls with keyword ", query_list)
    for query in query_list:
        startIndex = 1  # 시작 인덱스
        while (True):
            try:

                if len(except_keyword_list) >= 1:
                    if len(required_keyword_list) >= 1: # case 1 (True True)
                        result = service.cse().list(
                            q=query,  # 검색 키워드
                            cx='001132580745589424302:jbscnf14_dw',  # CSE Key
                            lr='lang_ko',  # 검색 언어 (한국어)
                            start=startIndex,
                            filter="0",
                            excludeTerms=' '.join(except_keyword_list),
                            exactTerms=' '.join(required_keyword_list)
                        ).execute()
                    else: # case 2 (True False)
                        result = service.cse().list(
                            q=query,  # 검색 키워드
                            cx='001132580745589424302:jbscnf14_dw',  # CSE Key
                            lr='lang_ko',  # 검색 언어 (한국어)
                            start=startIndex,
                            filter="0",
                            excludeTerms=' '.join(except_keyword_list)
                        ).execute()
                else:
                    if len(required_keyword_list) >= 1: # case 3 (False True)
                        result = service.cse().list(
                            q=query,  # 검색 키워드
                            cx='001132580745589424302:jbscnf14_dw',  # CSE Key
                            lr='lang_ko',  # 검색 언어 (한국어)
                            start=startIndex,
                            filter="0",
                            exactTerms=' '.join(required_keyword_list)
                        ).execute()
                    else: # case 4 (False False)
                        result = service.cse().list(
                            q=query,  # 검색 키워드
                            cx='001132580745589424302:jbscnf14_dw',  # CSE Key
                            lr='lang_ko',  # 검색 언어 (한국어)
                            start=startIndex,
                            filter="0"
                        ).execute()

                # 검색된 결과가 있을 때
                if "items" in result:
                    for item in result["items"]:
                        url = item["link"]
                        response_url.append(url)

                    # INDEX 이동
                    if (len(result["items"]) < 10):  # 결과가 10개 미만이면 STOP
                        break
                    else:  # 결과가 10개면 이동
                        startIndex = startIndex + 10
                else:
                    # print("No more Results")
                    break
            except Exception as e:
                break

    # remove urls duplicate without protocol
    for url in response_url:
        if "https://" in url:
            if url.replace("https://", "http://") in response_url:
                response_url.remove(url)
        elif "http://" in url:
            if url.replace("http://", "https://") in response_url:
                response_url.remove(url)

    response_url = np.unique(response_url).tolist()

    print("The number of all results : " + str(len(response_url)))

    return response_url

'''
검색 결과 URL 분류 함수
'''
def classify_url(url_list):
    """ Extract urls  for exclusion from all url list """
    # print("3. classify page urls")

    file_check = ["download", "down", "file", "pdf", "excel", "xlsx", "docx", "hwp"]

    download_list = []
    html_list = []
    except_list = []

    for i, url in enumerate(url_list):
        # extract downloadable URL (only pdf)
        if any(ext in url.lower() for ext in file_check) :
            if identify_file_format(url) == "pdf":
                download_list.append(url)
        elif (any(ext in url.lower() for ext in ["youtube", "movie.daum.net", "wikipedia", "play.google.com", "itunes.apple.com"])):
            except_list.append(url)
        else:
            html_list.append(url)

    print("All : " + str(len(url_list)) + " ( HTML URL : " + str(len(html_list)) + " / Downloadable URL : " + str(
        len(download_list)) + " )")
    return download_list, html_list, except_list

'''
검색 결과 URL 필터링 함수
'''
def extract_parsable_urls(keyword_list, except_keyword_list, required_keyword_list):

    # google custom search and get urls related with the keyword
    url_list = google_search(keyword_list, except_keyword_list, required_keyword_list)

    # remove urls for exclusion
    download_list, html_list, except_list = classify_url(url_list)

    return download_list, html_list, except_list

'''
STRING 변수 내 특정 SUBSTRING이 포함된 위치를 모두 반환하는 함수
'''
def locations_of_substring(string, substring):
    """ Return a list of locations of a substring """

    substring_length = len(substring)
    def recurse(locations_found, start):
        location = string.find(substring, start)
        if location != -1:
            return recurse(locations_found + [location], location+substring_length)
        else:
            return locations_found

    return recurse([], 0)

'''
조사 제거 함수
'''
def remove_postposition(word):
    if word[-3:] == "에서는":
        return word[:-3]
    elif word[-2:] in ["에서", "이다", "으로", "과의"]:
        return word[:-2]
    # elif word[-1:] in ["은", "는", "이", "가", "의"]:
    elif word[-1:] in ["은", "는", "의", "과"]:
        return word[:-1]
    else:
        return word

'''
불필요한 HTML 태그 제거 함수
'''
def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True

'''
HTML 파싱 함수
'''
def parse_html(url):

    headers = {
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'en-US,en;q=0.8',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
    }

    regex = re.compile('.*footer.*')

    footer = ""

    """ Parse html and remove unnecessary part of the document """
    try:
        response = rs.get(url, headers=headers, allow_redirects=False)
        for i in response.history:
            print(i.url)
        if response.encoding != None:
            html = response.text.encode(response.encoding)
        else:
            html = response.text
    except Exception as e:
        return None, None, None, None, None

    # browser = webdriver.PhantomJS()
    # html = browser.page_source

    soup = BeautifulSoup(html, 'html.parser')

    if soup.title is not None :
        title = soup.title.get_text().strip()
        title = re.sub(r'([\s])\1+', r'\1', title) # remove duplicate white space characters
    else :
        title = ""


    if soup == None: return None, None, None, None, None

    # filter soup
    # [tag.decompose() for tag in soup(["script", "style", "head", "title", "meta", "[document]"])]

    # remove hidden elements
    [e.extract() for e in soup.select('[style~="display:none"]') + soup.select('[style~="visibility:hidden"]')]

    #########################################

    # remove div with "footer" class
    for div in soup.find_all(class_=regex):
        if footer != "":
            footer.append(div.extract())
        else:
            footer = div.extract()

    for div in soup.find_all(id=regex):
        if footer != "":
            footer.append(div.extract())
        else:
            footer = div.extract()

    # remove "footer" element
    if soup.find("footer") != None:
        if footer != "":
            footer.append(soup.find("footer").extract())
        else:
            footer = soup.find("footer").extract()

    html_soup = copy.copy(soup)
    footer_soup = copy.copy(footer)

    # 문단 태그 앞 뒤 공백 라인 문자(\n) 추가

    for tag in soup.find_all("p"):
        original_text = tag.get_text()
        if original_text is not None:
            tag.string = "\n" + original_text + "\n"

    # 줄바꿈 태그 처리
    for tag in soup.find_all("br"):
        tag.replaceWith("\n")

    for tag in soup.find_all("li"):
        original_text = tag.get_text()
        if original_text is not None:
            tag.string = "\n" + original_text + "\n"

    # extract only text
    html_text = u" ".join(t for t in filter(tag_visible, soup.findAll(text=True))).strip().lower()

    if footer == "":
        footer_text = ""
    else:
        footer_text = u" ".join(t for t in footer.findAll(text=True)).strip().lower()

    return html_soup, html_text, footer_soup, footer_text, title


def find_substring(substring, string):
    '''
    Returns list of indices where substring begins in string

    find_substring("me", "The cat says meow, meow")
    [13, 19]
    '''
    indices = []
    index = -1  # Begins at -1 so index + 1 is 0
    while True:
        # Find next index of substring, by starting search from index + 1
        index = string.find(substring, index + 1)
        if index == -1:
            break  # All occurrences have been found
        indices.append(index)
    return indices

'''
조건식 파싱 함수
'''
def parse_condition_expression(query):

    exceptre = re.compile('-([ ()and\u3131-\u3163\uac00-\ud7a3]+)')
    requirere = re.compile('\+([ ()and\u3131-\u3163\uac00-\ud7a3]+)')
    results, except_words, require_words = [], [], []

    # 1. "-" operator
    if query.find("-") != -1:
        excepts = exceptre.findall(query)
        for e in excepts:
            words = e.strip()
            if words.find("(") != -1:
                words = words.replace("(", "").replace(")", "").strip()
                words = re.split("and", words)
                for w in words:
                    except_words.append(w.strip())
            else:
                except_words.append(words)

    # 2. "+" operator
    if query.find("+") != -1:
        requires = requirere.findall(query)
        for r in requires:
            words = r.strip()
            if words.find("(") != -1:
                words = words.replace("(", "").replace(")", "").strip()
                words = re.split("and", words)
                for w in words:
                    require_words.append(w.strip())
            else:
                require_words.append(words)

    query = re.sub(exceptre, "", query)
    query = re.sub(requirere, "", query)

    # 3. "()"
    parenre = re.compile('\([ andor\u3131-\u3163\uac00-\ud7a3]+\)')
    parens = parenre.findall(query)
    paren_dict = {}
    for i, p in enumerate(parens):
        query = query.replace(p, str(i))
        paren_dict[str(i)] = p

    # 4. "and", "or"
    if query.find("and") != -1:
        words = re.split("and", query)
        for i, w in enumerate(words):
            words[i] = w.strip()

        if len(paren_dict) != 0:
            for k in paren_dict:
                if paren_dict[k].find("and") != -1:
                    paren_words = []
                    for a in paren_dict[k].replace("(", "").replace(")", "").split("and"):
                        paren_words.append(a.strip())
                    if len(words) - 1 > words.index(k):
                        temp = words[words.index(k) + 1:]
                        words = words[:words.index(k)] + paren_words + temp
                    else:
                        words = words[:words.index(k)] + paren_words
                    results.append(' '.join(words))
                else:
                    for a in paren_dict[k].replace("(", "").replace(")", "").split("or"):
                        words_bak = copy.deepcopy(words)
                        temp = a.strip()
                        words_bak[words_bak.index(k)] = temp
                        results.append(' '.join(words_bak))
        else:
            results.append(' '.join(words))

    print("results :", results)
    print("except_words :", except_words)
    print("require words :", require_words)

    return results, except_words, require_words

'''
DB에 연결한 후 CURSOR를 반환하는 함수
'''
def augment_keyword_alternatives(keyword_list, related_keyword_list):

    '''
    관련 키워드 확장 함수
    :param keyword: 검색 키워드, string
    :param keyword_alternatives: 검색 키워드 관련 키워드, list
    :return: 확장된 키워드 목록, list
    '''
    res = []
    k_list = keyword_list + related_keyword_list

    for item in k_list:
        if " " in item:
            res.extend(item.split(" "))
            res.append(''.join(item))
        else:
            res.append(item)

    res = [x.lower() for x in res]

    return list(np.unique(res))

'''
DB에 연결한 후 CURSOR를 반환하는 함수
'''
def connect_db():

    conn = pymysql.connect(host="211.180.114.131", user="user", password="!J12341234", db="company_search",
                           charset="utf8")

    cursor = conn.cursor()

    return cursor

# 기업 DB를 사용하여 기업을 검색하였을 때 사용
def select_company_info(cursor, company_name):

    sql = 'select company_type, business_type, website_url, contact_number from company_db where company_name = "{0}"'.format(company_name)

    try:
        cursor.execute(sql)
    except Exception as e:
        print(e)

    rows = cursor.fetchall()

    return rows[0][0], rows[0][1], rows[0][2], rows[0][3]

# 패턴을 사용하여 기업을 검색하였을 때 사용
def select_company_info2(cursor, company_name):

    sql = "select idx, company_name from company_db order by idx"

    try:
        cursor.execute(sql)
    except Exception as e:
        print(e)

    rows = cursor.fetchall()

    name_df = pd.DataFrame(list(rows), columns = ["idx", "company_name"])

    name_df["company_name_flatten"] = [a.split("/") for a in name_df["company_name"]]

    found_idx = ""

    for i in range(0, len(name_df)):
        for j in range(0, len(name_df["company_name_flatten"][i])):
            if name_df["company_name_flatten"][i][j].replace("(주)", "") == company_name :
                found_idx = name_df["idx"][i]

    if found_idx == "": return "-", "-", "-", "-", "-"

    sql = 'select company_name, company_type, business_type, website_url, contact_number from company_db where idx = "{0}"'.format(found_idx)

    try:
        cursor.execute(sql)
    except Exception as e:
        print(e)

    rows = cursor.fetchall()

    return rows[0][0], rows[0][1], rows[0][2], rows[0][3], rows[0][4]

'''
기업 검색 결과 DICTIONARY 변수 업데이트 함수
'''
def update_company_count_dict(cursor, company, url, title, db_exist, case, paragraph):

    if case != 1 : case = 0

    # 패턴으로 찾은 경우 DB에 기업 정보 있는지 확인
    if db_exist != True:
        company_name, company_type, business_type, website_url, contact_number = select_company_info2(cursor, company)
        if (company_name, company_type, business_type, website_url, contact_number) != ('-', '-', '-', '-', '-'): # DB에 있는 경우
            db_exist = True
            company = company_name

    if company in company_count_dict:
        company_count_dict[company]["count"] += 1
        company_count_dict[company]["url_list"].append(url)
        company_count_dict[company]["title_list"].append(title)
        company_count_dict[company]["paragraph_list"].append(paragraph)
        company_count_dict[company]["case_list"].append(case)
    else:
        if db_exist == True:
            company_type, business_type, website_url, contact_number = select_company_info(cursor, company)
            db_exist_code = "1"
        else :
            company_type, business_type, website_url, contact_number = "-", "-", "-", "-"
            db_exist_code = "0"

        company_count_dict[company] = {"count": 1,
                                                "url_list": [url],
                                                "title_list": [title],
                                                "db_exist": db_exist_code,
                                                "company_type": company_type,
                                                "business_type": business_type,
                                                "website_url": website_url,
                                                "contact_number": contact_number,
                                                "case_list" : [case],
                                                "paragraph_list":[paragraph]}

    return company_count_dict

'''
기업 검색 결과 DICTIONARY 변수 업데이트 함수
'''
def update_company_count_dict2(cursor, company, url, title, db_exist, case, paragraph):

    if case != 1: case = 0

    if company in company_count_dict2:
        company_count_dict2[company]["count"] += 1
        company_count_dict2[company]["url_list"].append(url)
        company_count_dict2[company]["title_list"].append(title)
        company_count_dict2[company]["paragraph_list"].append(paragraph)
        company_count_dict[company]["case_list"].append(case)
    else:
        if db_exist == True :
            company_type, business_type, website_url, contact_number = select_company_info(cursor, company)
        else :
            company_type, business_type, website_url, contact_number = "-", "-", "-", "-"

        if db_exist == True : db_exist_code = "1"
        else : db_exist_code = "0"

        company_count_dict2[company] = {"count": 1,
                                                "url_list": [url],
                                                "title_list": [title],
                                                "db_exist": db_exist_code,
                                                "company_type": company_type,
                                                "business_type": business_type,
                                                "website_url": website_url,
                                                "contact_number": contact_number,
                                                "case_list" : [case],
                                                "paragraph_list":[paragraph]}


    return company_count_dict2

'''
해당 기업명 포함 단락 내 키워드가 포함되었는지 확인하여 포함 여부와 포함된 키워드를 반환하는 함수 
'''
def check_keywords_exist_in_paragrah(paragraph, augmented_keyword_list):

    found = False

    # 해당 기업명 포함 단락 내 키워드가 포함되었는지 확인
    for ak in augmented_keyword_list :
        if ak in paragraph:
            found = True
            break

    return found, ak

'''
URL을 읽어 파일 확장자를 확인하는 함수
'''
def identify_file_format(url):
    file_format = ""

    if "pdf" in url:
        return "pdf"
    elif "hwp" in url:
        return "hwp"
    elif "docx" in url:
        return "docx"

    try:
        res = urllib.request.urlopen(url)
        content_type, _ = cgi.parse_header(res.headers.get("Content-type", ""))


        if content_type == "application/pdf":
            return "pdf"
        else:
            _, params = cgi.parse_header(res.headers.get("Content-Disposition", ""))
            if "filename" in params :
                filename = params["filename"]
                if "pdf" in filename:
                    return "pdf"
                elif "hwp" in filename:
                    return "hwp"
                elif "docx" in filename:
                    return "docx"

    except Exception as e:
        return ""

    return file_format

'''
PDF 파일 내 텍스트를 모두 추출하여 반환하는 함수
'''
def pdf_convert(fname):

    output = StringIO()
    manager = PDFResourceManager()
    converter = TextConverter(manager, output, laparams=LAParams())
    interpreter = PDFPageInterpreter(manager, converter)

    infile = open(fname, 'rb')
    try :
        for i, page in enumerate(PDFPage.get_pages(infile, check_extractable=False)):
            interpreter.process_page(page)
    except PSEOF as e:
        return None

    infile.close()
    converter.close()
    text = output.getvalue()
    output.close
    return text


def process_pdf(pdf_content):

    num  = 0
    for res in re.finditer(r"[\w_]\n{1,2}[\w_]", pdf_content):
        start = res.start()
        end = res.end()
        pdf_content = pdf_content[:start - num] + \
                      pdf_content[start - num:end - num].replace("\n", "").replace("\n", "") + \
                      pdf_content[end - num:]
        num += res.group().count("\n")

    return pdf_content

