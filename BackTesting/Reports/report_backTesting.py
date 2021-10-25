
import os

import pandas as pd

from pykrx import stock

from datetime import datetime, timedelta

from mpl_finance import candlestick_ohlc

import matplotlib.pyplot as plt
import matplotlib.font_manager as plt_fm
import matplotlib.dates as mdates

from urllib.request import urlopen
from bs4 import BeautifulSoup
import requests

from selenium import webdriver

import time


font_path = "./font/godoFont_all/godoMaum.ttf"
font_prop = plt_fm.FontProperties(fname=font_path, size=18)


def get_unit_bid_price(code):
    opt = webdriver.ChromeOptions()
    opt.add_argument('headless')

    drv = webdriver.Chrome('./chromedriver.exe', options=opt)
    drv.implicitly_wait(3)
    base_url = 'https://finance.naver.com/item/sise.nhn?code='
    code = str(code)
    drv.get(base_url+code)

    bs = BeautifulSoup(drv.page_source, 'lxml')
    drv.quit()

    temp = bs.find_all('table', class_='type2')[1]
    sub_temp = temp.find_all('span', class_='tah p11 nv01')

    return int(sub_temp[1].get_text().strip().replace(',', '')) - int(sub_temp[3].get_text().strip().replace(',', ''))


def get_reports():
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
        for page in range(1, page_limit + 1):
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
                        company_list = ['하나금융투자', '이베스트증권', 'IBK투자증권', '미래에셋증권', '키움증권']
                        - 목표가 제시                    
                        """

                        if company not in company_list:
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


"""
매개변수
1) key = 'code'
stocks['code']: [list1, list2, list3, ...]
list1: 증권사1의 report list of (date, tp, opi)
2) key = '증권사'
stocks = [dict1, dict2, dict3, ...]
dict1: 증권사1의 dict
dict['code']: [(date1, tp1, opi1), date2, tp2, opi2), ...]
"""
def read_reports(fromDate, toDate, key='code'):
    global num_company
    if key == 'code':
        df = pd.read_excel('reports.xlsx', engine='openpyxl', index_col=0)
        df = df.sort_values(by='date', ascending=True)
        df['code'] = df['code'].map('{:06d}'.format)

        stocks = dict()

        for i in range(len(df)):
            data = df.iloc[i]
            code = data['code']
            date = data['date']
            tp = data['target price']
            opi = data['opinion']

            # fromDate ~ toDate 외의 데이터 제외
            fromDate = datetime.strptime(fromDate, "%Y%m%d").date()
            toDate = datetime.strptime(toDate, "%Y%m%d").date()
            date_d = datetime.strptime(date, "%y.%m.%d").date()
            if not fromDate < date_d < toDate:
                continue

            if not stocks.get(code):
                stocks[code] = [[] for _ in range(num_company)]

            for j in range(num_company):
                if company_list[j] == data['company']:
                    break
            stocks[code][j].append((date, tp, opi))

    elif key == '증권사':
        df = pd.read_excel('reports.xlsx', engine='openpyxl', index_col=0)
        df = df.sort_values(by='date', ascending=True)
        df['code'] = df['code'].map('{:06d}'.format)

        stocks = []
        for i in range(num_company):
            stocks.append(dict())

        for i in range(len(df)):
            data = df.iloc[i]
            code = data['code']
            date = data['date']
            tp = data['target price']
            opi = data['opinion']

            # fromDate ~ toDate 외의 데이터 제외
            fromDate_d = datetime.strptime(fromDate, "%Y%m%d").date()
            toDate_d = datetime.strptime(toDate, "%Y%m%d").date()
            date_d = datetime.strptime(date, "%y.%m.%d").date()
            if not fromDate_d < date_d < toDate_d:
                continue

            for j in range(num_company):
                if company_list[j] == data['company']:
                    break
            if not stocks[j].get(code):
                stocks[j][code] = []
            stocks[j][code].append((date, tp, opi))

    return stocks


def plot_graph(fromDate, toDate):
    if not os.path.isdir('./graphs'):
        os.mkdir('./graphs')

    stocks = read_reports(fromDate=fromDate, toDate=toDate, key='code')
    for key, value in stocks.items():
        code = key
        """
        value[0]: 하나금융투자
        value[1]: 이베스트증권
        value[2]: IBK투자증권
        value[3]: 미래에셋증권
        value[4]: 키움증권
        """
        # 주가
        time.sleep(1)
        df = stock.get_market_ohlcv_by_date(fromDate, toDate, code)
        df['number'] = df.index.map(mdates.date2num)
        # 코스피
        kospi = stock.get_index_ohlcv_by_date(fromDate, toDate, "1001")
        kospi['number'] = kospi.index.map(mdates.date2num)
        # Empty df인 경우
        if df.empty:
            continue
        name = stock.get_market_ticker_name(code)
        # 거래 정지 기간 처리
        idx_list = df.index[df.시가 == 0]
        for idx in idx_list:
            close = df.loc[idx].종가
            df.at[idx, '시가'] = close
            df.at[idx, '고가'] = close
            df.at[idx, '저가'] = close
        ohlc = df[['number', '시가', '고가', '저가', '종가']]
        figure1 = plt.figure(1, figsize=(9, 9))
        p1 = plt.subplot(1, 1, 1)
        plt.title(code + ' ' + name)
        # plt.grid(True)
        candlestick_ohlc(p1, ohlc.values, width=.6, colorup='red', colordown='blue')
        p1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        for i in range(1, 2):
            for j in range(1, len(value[i])):
                val = value[i][j]
                day = val[0]
                tp = val[1]
                tp_past = value[i][j - 1][1]
                day = mdates.date2num(datetime.strptime(day, "%y.%m.%d").date())
                if tp > tp_past:
                    if i == 0:
                        plt.vlines(day, df.종가.min(), df.종가.max(), colors='green', linewidth=1)
                    elif i == 1:
                        plt.vlines(day, df.종가.min(), df.종가.max(), colors='pink', linewidth=1)
                    elif i == 2:
                        plt.vlines(day, df.종가.min(), df.종가.max(), colors='purple', linewidth=1)
                    elif i == 3:
                        plt.vlines(day, df.종가.min(), df.종가.max(), colors='grey', linewidth=1)
                    else:
                        plt.vlines(day, df.종가.min(), df.종가.max(), colors='orange', linewidth=1)
                    # plt.plot(day, df.종가.min(), 'r^')
        p2 = p1.twinx()
        p2.plot(kospi['number'], kospi['종가'], linewidth=1, label='KOSPI')
        plt.legend(loc='best')
        figure1.savefig(fname='./graphs/' + code, dpi=300)
        plt.close()


"""
매개 변수
upper: upper % 이상 -> 익절
lower: lower % 이하 -> 손절
duration: duration 일 이후 -> 매도
"""
def calculate_yields(fromDate, toDate, upper=50, lower=50, duration=90):
    stocks = read_reports(fromDate=fromDate, toDate=toDate, key='증권사')
    writer = pd.ExcelWriter('./yields.xlsx', engine='xlsxwriter')
    # i: 각 증권사
    for i in range(num_company):
        code_list = []
        yield_list = []
        for key, value in stocks[i].items():
            code = key
            # 주가
            today = datetime.strftime(datetime.now().date() - timedelta(days=10), "%Y%m%d")
            df = stock.get_market_ohlcv_by_date(fromDate, today, code)
            # 코스피
            #kospi = stock.get_index_ohlcv_by_date(fromDate, today, "1001")
            # Empty df인 경우
            if df.empty:
                continue
            # df의 start date 및 end date check
            if df.index[0] - datetime.strptime(fromDate, "%Y%m%d") > timedelta(days=10):
                continue
            if df.index[-1] < datetime.strptime(today, "%Y%m%d") - timedelta(days=10):
                continue
            name = stock.get_market_ticker_name(code)
            # 거래 정지 기간 처리
            idx_list = df.index[df.시가 == 0]
            for idx in idx_list:
                close = df.loc[idx].종가
                df.at[idx, '시가'] = close
                df.at[idx, '고가'] = close
                df.at[idx, '저가'] = close
    
            index_list = df.index
            """
            매수 알고리즘: 증권사 목표 주가 상향
            --> 익일 시가 매수
            [(날짜1, 가격1), (날짜2, 가격2), ]
            날짜: datetime 객체 %Y-%m-%d
            """
            buy_report = []
            # val: 개별 리포트
            for idx in range(1, len(value)):
                val = value[idx]
                day = val[0]
                tp = val[1]
                tp_past = value[idx - 1][1]
                """
                증권사 목표 주가 상향한날짜 이후의 유효한 날짜 검색
                """
                while (True):
                    day = datetime.strptime(day, "%y.%m.%d").date() + timedelta(days=1)
                    if day in index_list:
                        break
                    day = datetime.strftime(day, "%y.%m.%d")
                day_s = datetime.strftime(day, "%Y-%m-%d")
                if tp > tp_past:
                    buy_report.append((day, df.loc[day_s]['시가']))
            """
            매도 알고리즘
            [(날짜1, 가격1), (날짜2, 가격2), ]
            날짜: datetime 객체 %Y-%m-%d
            """
            sell_report = []
            for buy in buy_report:
                day = buy[0]
                price = buy[1]
                upper_limit = price * (1 + upper/100)
                lower_limit = price * (1 - lower/100)
                # unit_bid = get_unit_bid_price(code)
                # if upper_limit % unit_bid == 0:
                #     upper_price = upper_limit
                # else:
                #     upper_price = (upper_limit + unit_bid) // unit_bid * unit_bid
                # if lower_limit % unit_bid == 0:
                #     lower_price = lower_limit
                # else:
                #     lower_price = (lower_limit - unit_bid) // unit_bid * unit_bid
                # 6개월 내에 + upper 혹은 - lower 매도 조건 check
                sell_flag = False
                for count in range(duration):
                    # 개장일이 아니라면 pass
                    if not day in index_list:
                        day = day + timedelta(days=1)
                        continue
                    # 개장일이라면 매도 조건 확인
                    day_s = datetime.strftime(day, "%Y-%m-%d")
                    # 익절 조건 확인
                    if df.loc[day_s]['저가'] < upper_limit < df.loc[day_s]['고가']:
                        sell_report.append((day, upper_limit))
                        sell_flag = True
                        break
                    # 손절 조건 확인
                    if df.loc[day_s]['저가'] < lower_limit < df.loc[day_s]['고가']:
                        sell_report.append((day, lower_limit))
                        sell_flag = True
                        break
                    # 익절/손절 조건 발생하지 않은 경우
                    day = day + timedelta(days=1)
                # duration 동안 익절/손절 조건 발생하지 않은 경우
                # 개장일 체크
                while (True):
                    if day in index_list:
                        break
                    day = day + timedelta(days=1)
                day_s = datetime.strftime(day, "%Y-%m-%d")
                if not sell_flag:
                    sell_report.append((day, df.loc[day_s]['종가']))

            # 수익률 계산
            strat_yield_with_fee = 1
            for idx in range(len(buy_report)):
                delta = (0.99685 * sell_report[idx][1] - 1.00315 * buy_report[idx][1]) / buy_report[idx][1]
                strat_yield_with_fee = strat_yield_with_fee * (1 + delta)

            code_list.append(code)
            yield_list.append(strat_yield_with_fee)

        data = {'code': code_list, 'yields': yield_list}
        dd = pd.DataFrame(data=data)
        #writer = pd.ExcelWriter('./yields.xlsx', engine="openpyxl", mode='a')
        dd.to_excel(writer, sheet_name=company_list[i])
    writer.close()


"""
증권사 리스트 지정
"""
num_company = 5
company_list = ['하나금융투자', '이베스트증권', 'IBK투자증권', '미래에셋증권', '키움증권']

fromDate = '20170101'
toDate = '20200930'

#get_reports()
#plot_graph(fromDate=fromDate, toDate=toDate)
calculate_yields(fromDate=fromDate, toDate=toDate)
