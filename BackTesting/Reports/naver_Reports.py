from urllib.request import urlopen
from bs4 import BeautifulSoup
import requests
import pandas as pd


url = "https://finance.naver.com/research/company_list.nhn?&page="

with urlopen(url) as doc:
    html = BeautifulSoup(requests.get(url, headers={'User-agent': 'Mozilla/5.0'}).text, 'lxml')
    pgrr = html.find('td', class_='pgRR')
    s = str(pgrr.a['href']).split('=')
    last_page = s[-1]

    code_lists = []
    name_lists = []
    link_lists = []
    title_lists = []
    company_lists = []
    pdf_lists = []
    date_lists = []
    price_lists = []
    opi_lists = []

    page_limit = 1000
    for page in range(1, page_limit+1):
        page_url = url + str(page)
        with urlopen(page_url) as doc:
            html = BeautifulSoup(requests.get(page_url, headers={'User-agent': 'Mozilla/5.0'}).text, 'lxml')
            html = html.find('table', class_="type_1")
            lists = html.find_all('tr')
            lists = lists[2:]

            for i in range(len(lists)):
                if lists[i].td.get_text() != '':
                    code = lists[i].a['href'].split('=')[-1]
                    name = lists[i].a['title']
                    link = "https://finance.naver.com/research/" + \
                           lists[i].find_all('td')[1].a['href']
                    title = lists[i].find_all('td')[1].a.get_text()
                    company = lists[i].find_all('td')[2].get_text()
                    if lists[i].find_all('td')[3].a:
                        pdf = lists[i].find_all('td')[3].a['href']
                    else:
                        pdf = "N/A"
                    date = lists[i].find_all('td')[4].get_text()
                    with urlopen(link) as doc:
                        html = BeautifulSoup(requests.get(link, headers={'User-agent': 'Mozilla/5.0'}).text, 'lxml')
                        html = html.find('div', class_='view_info')
                        price = html.em.get_text().replace(',', '')
                        opi = html.find('em', class_='coment').get_text()

                    """
                    포함 조건
                    - 유효한 증권 회사의 리포트
                    effective_companys = ['하나금융투자', '이베스트증권', 'IBK투자증권', '미래에셋증권',
                                          '케이프투자증권', '키움증권']
                    - 목표가 제시                    
                    """

                    effective_companys = ['하나금융투자']

                    if company not in effective_companys:
                        continue
                    if price == '없음':
                        continue

                    code_lists.append(code)
                    name_lists.append(name)
                    link_lists.append(link)
                    title_lists.append(title)
                    company_lists.append(company)
                    pdf_lists.append(pdf)
                    date_lists.append(date)
                    price_lists.append(price)
                    opi_lists.append(opi)

    data = {'code': code_lists, 'stock': name_lists, 'link': link_lists, 'title': title_lists,
            'company': company_lists, 'pdf': pdf_lists, 'date': date_lists, 'target price': price_lists,
            'opinion': opi_lists}
    df = pd.DataFrame(data=data)
    df = df.sort_values(by='code', ascending=True)
    writer = pd.ExcelWriter('./reports.xlsx', engine='xlsxwriter')
    df.to_excel(writer)
    writer.close()


