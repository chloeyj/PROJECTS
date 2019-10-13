'''
Updated on 2018.10.22
'''

from app.module import *
import pandas as pd
import itertools
import numpy as np
import datetime, time
import sys
from app.utils import *

A = ["은", "는", "이", "가", "의", "와", "과", "를", "도"]
B = ["에서", "사가", "사는", "과의"]
C = ["입니다", "사에서", "사에서"]
news_keywords = ["news", "뉴스", "신문", "일보", "방송", "발행"]
shop_keywords = ["쇼핑"]





sys.setrecursionlimit(10000)

@shared_task(bind=True, throws=(Terminated,))
def main(self, keyword_list, related_keyword_list, required_keyword_list, except_keyword_list, doc_to_extract):
    start_time = time.time()
    '''
    메인 함수
    :param keyword: 검색 키워드 (Google Custom Search API q parameter value), string
    :param keyword_alternatives: 검색 키워드 관련 키워드, list
    :param condition: 조건 검색 여부, "True" or "False", string
    :param syn: 유사어 확장 검색 여부, "True", or "False", string
    :return: 검색 결과, dictionary
    '''
    progress_recorder = ProgressRecorder(self)

    '''
    초기 변수 설정
    '''

    # initialize a variable
    tempre, tempre2, tempre3, subject_postpositions1, subject_postpositions2, patterns1, patterns2, augmented_keyword_list, company_list, cursor, sc_seperators = init_variables(
        keyword_list, related_keyword_list)

    # initialize count dictionary variable
    company_count_dict, company_count_dict2 = init_count_dict()

    progress_recorder.set_progress(5, 100)

    '''
    URL 수집 및 정제
    '''

    download_list, html_list, except_list = extract_parsable_urls(keyword_list, except_keyword_list, required_keyword_list)

    # html_list = ["http://www.hellodd.com/?md=news&mt=view&pid=64694"]

    # HTML, PDF 파싱 여부 설정
    if doc_to_extract[0] == False : html_list = []
    if doc_to_extract[1] == False : download_list = []

    progress_recorder.set_progress(10, 100)

    '''
    기업 검색
    '''

    ####################################################################################################################
    #################   HTML   #########################################################################################
    ####################################################################################################################

    # parse the file and find the company name
    for i, url in enumerate(html_list):

        found_company_list, found_index_list = [], []

        print("URL", str(i) + ". " + url)

        # parse html
        html_soup, html_text, footer_soup, footer_text, title = parse_html(url)

        if html_text == None: continue

        '''
                특수 사이트
        '''
        # 롯데닷컴 제조사 추출 (상품 내 브랜드명만 추출)
        if "www.lotte.com" in url:
            if len(html_soup.select("#result")) != 0:
                result_div = html_soup.select("#result")[0]
                prod_div = result_div.select(".contents")
                for div in prod_div:
                    prod_name = div.a.strong
                    if prod_name is not None:
                        brand_name = prod_name.string.replace("[", "").replace("]", "")
                        brand_name = re.sub(r'\([^)]*\)', '', brand_name)
                        if (brand_name in ["기타브랜드"]) | (brand_name in found_company_list): continue

                        print("Case lotte.com)", brand_name)

                        company_count_dict = update_company_count_dict(cursor, brand_name, url, title,
                                                                       False, 0, brand_name)  # update company count dict

                        found_company_list.append(brand_name)

            continue

        # 잡플래닛 내 기업명 추출
        if "www.jobplanet.co.kr" in url:
            if len(html_soup.select(".company_info")) != 0:
                company_name = html_soup.select_one(".company_info").select_one(".tit")
                if company_name is not None :
                    company_name = company_name.string
                    print("Case Job Planet)", company_name)

                    company_count_dict = update_company_count_dict(cursor, company_name, url, title, False, 0, company_name)

                    found_company_list.append(company_name)

            continue

        # 나머지 사이트

        for company_with_dash in company_list:

            company_original = company_with_dash

            found = False

            for company in company_with_dash.split("/"):

                '''
                Case 1) 기업 DB 사용, "(주)" 포함
                '''

                company = company.replace("(주)", "")  # "(주)" 제거

                # 본문 내 검색
                if company in html_text:
                    patterns0 = [r'[\W_](%s)(%s)[\W_]' % (company, '|'.join(subject_postpositions1)),
                                 r'[\W_](%s)[%s][\W_]' % (company, '|'.join(subject_postpositions2)),
                                 r'(\(주\)|\(주\) |㈜|㈜ )(%s)(%s)[\W_]' % (company, '|'.join(subject_postpositions1)),
                                 r'(\(주\)|\(주\) |㈜|㈜ )(%s)[%s][\W_]' % (company, '|'.join(subject_postpositions2)),
                                 r'[\W_](%s)[\W_]' % company]

                    for j, pattern in enumerate(patterns0):
                        if found is True: break
                        for res in re.finditer(pattern, html_text):  # 본문만

                            # 해당 기업명 포함 단락 및 기업명 추출
                            cor_word_area = res.group()
                            cor_word = re.findall(pattern, cor_word_area)[0]
                            if j == 0:
                                cor_word = cor_word[0]
                            elif j in [2, 3]:
                                cor_word = cor_word[1]

                            cor_word_paragraph = [ss.group() for ss in
                                                  re.finditer(r"([^\n^\t^\r]*?" + cor_word + r"[^\n^\t^\r]*)",
                                                              html_text) if
                                                  (ss.start() - 1 <= res.start()) & (ss.end() + 1 >= res.end())][0].strip()

                            found, coappear_keyword = check_keywords_exist_in_paragrah(cor_word_paragraph,
                                                                                       augmented_keyword_list)

                            if found is not True:
                                # print(
                                #     '"' + company + '" does not exist with keyword in sentence (' + cor_word_paragraph + ') -> keyword list : ' + str(
                                #         augmented_keyword_list))
                                pass
                            else:
                                print(
                                    '"' + company + '" exists with keyword in sentence (' + cor_word_paragraph + ') -> keyword : ' + coappear_keyword)
                                print("Case 1-A)", company_original)
                                company_count_dict = update_company_count_dict(cursor, company_original, url, title,
                                                                               True, 1, cor_word_paragraph)  # update company count dict

                                found_company_list.append(company_original)
                                break

                    if found is True: break

                # footer 내 검색 (영역 내 키워드 포함 여부 고려 X)
                if company in footer_text:
                    if company in ["페이스북", "facebook"]: continue  # footer 내에서는 페이스북 제외
                    if any([True for item in news_keywords + shop_keywords if item in footer_text]): continue # 뉴스 키워드 제외

                    # (주)000 / 000(주) / 000 / 주식회사 000 모두 고려한 정규식
                    ju_reg_find_list = [re.finditer('[\(주\)|㈜]{0,1}\s{0,1}(%s) ' % company, footer_text),
                                        re.finditer(' (%s)\s{0,1}[\(주\)|㈜]{0,1}' % company, footer_text)]

                    for j, ju_reg_find in enumerate(ju_reg_find_list):
                        if found is True: continue
                        for ju_reg_item in ju_reg_find:
                            if j == 0:
                                check_idx = ju_reg_item.start() - 1
                            else:
                                check_idx = ju_reg_item.end()

                            if len(footer_text) == check_idx:
                                found = True
                            else:
                                if footer_text[check_idx] in [" ", "\n", "\r", "\t", "\xa0"]:
                                    found = True

                            if found is True:
                                print("Case 1-B)", company_original)
                                company_count_dict = update_company_count_dict(cursor, company_original, url, title,
                                                                               True, 1, company)  # update company count dict

                                found_company_list.append(company_original)
                                break


        '''
            Case 3) 기업 DB에 없는 기업명 추출 방법 1 -  기업명 등장 패턴으로 찾기
        '''

        for j, pattern in enumerate(patterns1):
            for res in re.finditer(pattern, html_text):  # 본문에서만

                found_company_list_flatten = [item.replace("(주)", "") for item in
                                              list(itertools.chain(*[c.split("/") for c in found_company_list]))]

                cor_word_area = res.group()
                cor_word = re.findall(pattern, cor_word_area)[0]
                if j in [0, 1, 6, 7]: cor_word = cor_word[1]
                elif j == 2 : cor_word = cor_word[0]
                elif j == 5 :
                    cor_word = cor_word[0]
                    if "," in cor_word:
                        cor_word = [e.strip() for e in cor_word.split(",")]
                    elif "·" in cor_word:
                        cor_word = [e.strip() for e in cor_word.split("·")]
                    else:
                        cor_word = [cor_word.strip()]

                if type(cor_word) == str: cor_word = [cor_word]

                for g, each in enumerate(cor_word):

                    found = False

                    # 해당 기업명 포함 단락 내 키워드가 포함되었는지 확인

                    try :
                        cor_word_paragraph = [ss.group() for ss in
                                          re.finditer(r"([^\n^\t^\r]*?" + each + r"[^\n^\t^\r]*)",
                                                      html_text) if
                                          (ss.start() - 1 <= res.start()) & (ss.end() + 1 >= res.end())][0].strip()
                    except Exception as e:
                        continue
                        # if "unbalanced parenthesis" in str(e):
                        #     print(cor_word_area)
                        #     print(cor_word)
                        #     cor_word_paragraph = [ss.group() for ss in
                        #                           re.finditer(r"([^\n^\t^\r]*?" + each + r"[^\n^\t^\r]*)",
                        #                                       html_text) if
                        #                           (ss.start() - 1 <= res.start()) & (ss.end() + 1 >= res.end())][
                        #         0].strip()
                        #     each = re.findall(r'\(.*' + each + '\)', cor_word_paragraph)[0].replace("(", "").replace(")", "")


                    found, coappear_keyword = check_keywords_exist_in_paragrah(cor_word_paragraph,
                                                                               augmented_keyword_list)


                    if found is not True:
                        # print(
                        #     '"' + each + '" does not exist with keyword in sentence (' + cor_word_area + ') -> keyword list : ' + str(
                        #         augmented_keyword_list))
                        pass
                    else:

                        # remove all strings in parenthesis with it and remove "(주)"
                        p_temp_cor_word = re.sub(r'\([^)]*\)', '', each).replace("(주)", "").replace("㈜", "").strip()
                        # remove some special characters(%'‘’") and numeric characters
                        p_temp_cor_word = re.sub(r'[%%0-9\'‘’"]+', '', p_temp_cor_word)
                        p_temp_cor_word = remove_postposition(p_temp_cor_word)
                        if (p_temp_cor_word in found_company_list_flatten + noise_keywords) | (
                                len(p_temp_cor_word) < 2) | (len(re.findall(r'[A-Za-z]사', p_temp_cor_word)) != 0) : continue

                        each = p_temp_cor_word
                        if each in found_company_list_flatten: continue
                        # print(
                        # '"' + each + '" exists with keyword in sentence (' + cor_word_paragraph + ') -> keyword : ' + coappear_keyword)
                        print("Case 3)", each, "- Pattern", j)
                        company_count_dict = update_company_count_dict(cursor, each, url, title,
                                                                   False, 3, cor_word_paragraph)  # update company count dict

                        found_company_list.append(each)

        '''
        Case 4) 기업 DB에 없는 기업명 추출 방법 2 - 본문 내 정규 표현식("(주)", "㈜", "주식회사")으로 찾기
        '''

        for j, pattern in enumerate(patterns2): # 본문
            for res in re.finditer(pattern, html_text):

                found_company_list_flatten = [item.replace("(주)", "") for item in
                                              list(itertools.chain(*[c.split("/") for c in found_company_list]))]

                # 해당 기업명 포함 단락 및 기업명 추출
                cor_word_area = res.group()
                if j != 3 :
                    cor_word = re.findall(pattern, cor_word_area)[0][1]
                else :
                    cor_word = re.findall(pattern, cor_word_area)[0]

                if cor_word in found_company_list_flatten: continue

                cor_word_paragraph = [ss.group() for ss in
                                      re.finditer(r"([^\n^\t^\r]*?" + cor_word + "[^\n^\t^\r]*)",
                                                  html_text) if \
                                      (ss.start() - 1 <= res.start()) & (ss.end() + 1 >= res.end())][0].strip()

                # 해당 기업명 포함 단락 내 키워드가 포함되었는지 확인
                found, coappear_keyword = check_keywords_exist_in_paragrah(cor_word_paragraph, augmented_keyword_list)

                if found is not True:
                    # print(
                    #     '"' + cor_word + '" does not exist with keyword in sentence (' + cor_word_paragraph + ') -> keyword list : ' + str(
                    #         augmented_keyword_list))
                    pass
                else:

                    cor_word = remove_postposition(cor_word)
                    if (cor_word in found_company_list_flatten + noise_keywords) | (len(cor_word) < 2): continue

                    # print(
                    #     '"' + cor_word + '" exists with keyword in sentence (' + cor_word_paragraph + ') -> keyword : ' + coappear_keyword)
                    print("Case 4-A)", cor_word)
                    company_count_dict = update_company_count_dict(cursor, cor_word, url, title,
                                                                   False, 4, cor_word_paragraph)  # update company count dict

                    found_company_list.append(cor_word)

        for j, pattern in enumerate(patterns2): # footer
            if any([True for item in news_keywords + shop_keywords if item in footer_text]): break
            for res in re.finditer(pattern, footer_text):

                found_company_list_flatten = [item.replace("(주)", "") for item in
                                              list(itertools.chain(*[c.split("/") for c in found_company_list]))]

                # 해당 기업명 포함 단락 및 기업명 추출
                cor_word_area = res.group()
                if j != 3 :
                    cor_word = re.findall(pattern, cor_word_area)[0][1]
                else :
                    cor_word = re.findall(pattern, cor_word_area)[0]

                if cor_word in found_company_list_flatten: continue

                # 해당 기업명 포함 단락 내 키워드가 포함되었는지 확인
                found, coappear_keyword = True, ""

                cor_word = remove_postposition(cor_word)
                if (cor_word in found_company_list_flatten + noise_keywords) | (len(cor_word) < 2): continue

                print("Case 4-B)", cor_word)
                company_count_dict = update_company_count_dict(cursor, cor_word, url, title,
                                                                   False, 4, cor_word_area)  # update company count dict

                found_company_list.append(cor_word)

        # update process
        if doc_to_extract[1] == False:
            progress_recorder.set_progress(int((i + 1) * 90 / len(html_list)) + 10, 100)
        else:
            progress_recorder.set_progress(int((i + 1) * 70 / len(html_list)) + 10, 100)

    ####################################################################################################################
    #################   PDF   ##########################################################################################
    ####################################################################################################################

    for i, url in enumerate(download_list):

        title = ""

        found_company_list, found_index_list = [], []

        print("URL", str(i) + ". " + url)
        urllib.request.urlretrieve(url, "temp.pdf")
        pdf_content = pdf_convert("temp.pdf")
        if pdf_content is None: continue
        pdf_content = process_pdf(pdf_content)

        for company_with_dash in company_list:

            company_original = company_with_dash

            found = False

            for company in company_with_dash.split("/"):

                '''
                Case 1) 기업 DB 사용, "(주)" 포함
                '''

                company = company.replace("(주)", "")  # "(주)" 제거

                # 본문 내 검색
                if company in pdf_content:
                    patterns0 = [r'[\W_](%s)(%s)[\W_]' % (company, '|'.join(subject_postpositions1)),
                                 r'[\W_](%s)[%s][\W_]' % (company, '|'.join(subject_postpositions2)),
                                 r'(\(주\)|\(주\) |㈜|㈜ )(%s)(%s)[\W_]' % (company, '|'.join(subject_postpositions1)),
                                 r'(\(주\)|\(주\) |㈜|㈜ )(%s)[%s][\W_]' % (company, '|'.join(subject_postpositions2)),
                                 r'[\W_](%s)[\W_]' % company]

                    for j, pattern in enumerate(patterns0):
                        if found is True: break
                        for res in re.finditer(pattern, pdf_content):  # 본문만

                            # 해당 기업명 포함 단락 및 기업명 추출
                            cor_word_area = res.group()
                            cor_word = re.findall(pattern, cor_word_area)[0]
                            if j == 0:
                                cor_word = cor_word[0]
                            elif j in [2, 3]:
                                cor_word = cor_word[1]

                            cor_word_paragraph = [ss.group() for ss in re.finditer(
                                r"([^%s]*?" % sc_seperators + cor_word + r"[^%s]*)" % sc_seperators, pdf_content) \
                                                  if (ss.start() - 1 <= res.start()) & (ss.end() + 1 >= res.end())][
                                0].strip()

                            # found, coappear_keyword = check_keywords_exist_in_paragrah(cor_word_paragraph,
                            #                                                            augmented_keyword_list)

                            found, coappear_keyword = True, ""

                            if found is not True:
                                # print(
                                #     '"' + company + '" does not exist with keyword in sentence (' + cor_word_paragraph.strip() + ') -> keyword list : ' + str(
                                #         augmented_keyword_list))
                                pass
                            else:

                                # print(
                                #     '"' + company + '" exists with keyword in sentence (' + cor_word_paragraph.strip() + ') -> keyword : ' + coappear_keyword)
                                print("Case 1)", company_original)
                                company_count_dict2 = update_company_count_dict2(cursor, company_original, url, title,
                                                                               True, 1, cor_word_paragraph)  # update company count dict

                                found_company_list.append(company_original)
                                break

                    if found is True: break


        '''
            Case 3) 기업 DB에 없는 기업명 추출 방법 1 -  기업명 등장 패턴으로 찾기
        '''

        pattern_0_found = False
        for j, pattern in enumerate(patterns1):
            if (pattern_0_found == True) & (j == 1): continue  # Pattern0으로 찾았을 경우 Pattern1은 중복됨으로 skip
            for res in re.finditer(pattern, pdf_content):

                found_company_list_flatten = [item.replace("(주)", "") for item in
                                              list(itertools.chain(*[c.split("/") for c in found_company_list]))]

                cor_word_area = res.group()
                cor_word = re.findall(pattern, cor_word_area)[0]
                if j in [0, 1, 6, 7]:
                    cor_word = cor_word[1]
                elif j == 2 :
                    cor_word = cor_word[0]
                elif j == 5:
                    cor_word = cor_word[0]
                    if "," in cor_word:
                        cor_word = [e.strip() for e in cor_word.split(",")]
                    elif "·" in cor_word:
                        cor_word = [e.strip() for e in cor_word.split("·")]
                    else:
                        cor_word = [cor_word.strip()]

                if type(cor_word) == str: cor_word = [cor_word]

                # escape all "(" and ")" in string
                temp_cor_word_area = re.findall(pattern, cor_word_area)[0][0]
                temp_cor_word_area = re.sub(r"\(", r"\\(", temp_cor_word_area)
                temp_cor_word_area = re.sub(r"\)", r"\\)", temp_cor_word_area)

                cor_word_paragraph = [ss.group() for ss in
                                      re.finditer(r"([^%s]*?" % sc_seperators + temp_cor_word_area + r"[^%s]*)" % sc_seperators,
                                                  pdf_content)\
                                      if (ss.start() - 1 <= res.start()) & (ss.end() + 1 >= res.end())][0].strip()

                for g, each in enumerate(cor_word):

                    # 해당 기업명 포함 단락 내 키워드가 포함되었는지 확인
                    # found, coappear_keyword = check_keywords_exist_in_paragrah(cor_word_paragraph, augmented_keyword_list)
                    found, coappear_keyword = True, ""

                    if found is not True:
                        print(
                            '"' + each + '" does not exist with keyword in sentence (' + cor_word_paragraph + ') -> keyword list : ' + str(
                                augmented_keyword_list))
                        pass
                    else:
                        # remove all strings in parenthesis with it and remove "(주)"
                        p_temp_cor_word = re.sub(r'\([^)]*\)', '', each).replace("(주)", "").replace("㈜", "").strip()
                        # remove some special characters(%'‘’") and numeric characters
                        p_temp_cor_word = re.sub(r'[%%0-9\'‘’"]+', '', p_temp_cor_word)
                        p_temp_cor_word = remove_postposition(p_temp_cor_word)
                        if (p_temp_cor_word in [c.replace("(주)", "") for c in found_company_list] + noise_keywords) | (
                                    len(p_temp_cor_word) < 2): continue

                        if j == 0: pattern_0_found = True  # Pattern 0 으로 찾았을 경우 체크
                        each = p_temp_cor_word
                        if each in found_company_list_flatten: continue
                        # print(
                        #     '"' + cor_word + '" exists with keyword in sentence (' + cor_word_paragraph.strip() + ') -> keyword : ' + coappear_keyword)
                        print("Case 3)", each, "- Pattern", j)
                        company_count_dict2 = update_company_count_dict2(cursor, each, url, title,
                                                                       False, 3, cor_word_paragraph)  # update company count dict

                        found_company_list.append(each)

        # update process
        if doc_to_extract[0] == False:
            progress_recorder.set_progress(int((i + 1) * 90 / len(download_list)) + 10, 100)
        else:
            progress_recorder.set_progress(int((i + 1) * 20 / len(download_list)) + 80, 100)

    print("\n### 검색 결과 ###")
    print("### HTML 문서 ###")
    print("총", len(company_count_dict), "개,", list(company_count_dict.keys()))
    print("### PDF 문서 ###")
    print("총", len(company_count_dict2), "개,", list(company_count_dict2.keys()))

    # with open("ar_result.json", "w", encoding="utf-8") as f:
    #     json.dump(company_count_dict, f)

    now = datetime.datetime.now()
    nowDatetime = now.strftime('%Y-%m-%d_%H-%M')

    # df.to_csv("test_result/{0}_{1}.csv".format(keyword, nowDatetime), index=False)

    progress_recorder.set_progress(100, 100)

    end_time = time.time()
    running_time = end_time - start_time
    m, s = divmod(running_time, 60)



    # insert search info
    company_count_dict["search_info"] = {"html_url_num" : len(html_list), "pdf_url_num" : len(download_list), "all_url_num" : len(download_list) + len(html_list),
                                         "found_company_num_in_html" : len(company_count_dict),
                                         "found_url_num_in_html" : len(np.unique(list(itertools.chain(*[company_count_dict[item]["url_list"] for item in company_count_dict])))),
                                         "found_company_num_in_pdf" : len(company_count_dict2),
                                         "found_url_num_in_pdf" : len(np.unique(list(itertools.chain(*[company_count_dict2[item]["url_list"] for item in company_count_dict2])))),
                                         "found_company_num_in_all" : len(np.unique(list(company_count_dict) + list(company_count_dict2))),
                                         "running_time" : str(int(m)) + "분 " + str(int(s)) + "초"}

    return company_count_dict, company_count_dict2

# main("증강 현실", [], "False", "False", [True, False])

# main("증강 현실", ["가상 현실", "AR", "Augmented Reality", "Virtual Reality", "VR", "Mixed Reality", "MR"], "False", "False", [True, False])

# main("혈당 and (센서 or 측정)", ["측정", "당뇨", "기기"], "True", "False", [True, False])

# main("드론", [], "False", "False", [True, False])

# main("혈당 센서;혈당 탐지기;", [], "False", "True", [True, False])