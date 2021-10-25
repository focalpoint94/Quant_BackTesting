
from pykrx import stock

import pandas as pd

import matplotlib.pyplot as plt

from datetime import datetime, timedelta

from time import sleep

import numpy as np


"""
market: "KOSPI', "KOSDAQ" "MIX"
start_year: 투자 시작 연도 ('2014' ;str)
start_month: 투자 시작 월 ('11', ;str)
period: 'year', 'half year', 'quarter', 'month' ;str
"""
def smallStock_backTesting(market: str="KOSPI", start_year: str='2014', start_month: str='11', period: str='half year'):
    fromDate = start_year + start_month + "01"
    if period == 'year':
        duration = 365
        counter = 1
    elif period == 'half year':
        duration = 182
        counter = 2
    elif period == 'quarter':
        duration = 91
        counter = 4
    elif period == 'month':
        duration = 30
        counter = 12
    else:
        print(period + '는 지원되지 않습니다.')
        return

    this_fromDate = fromDate
    this_toDate = datetime.strftime(datetime.strptime(this_fromDate, "%Y%m%d")
                                    + timedelta(days=duration), "%Y%m%d")
    count = 0

    term_list = []
    profit_list = []

    while True:
        """ 1년 단위 날짜 보정 """
        if count == counter:
            this_fromDate = this_fromDate[:4] + start_month + "01"
            count = 0

        open_fromDate = stock.get_nearest_business_day_in_a_week(this_fromDate, prev=False)
        open_toDate = stock.get_nearest_business_day_in_a_week(this_toDate, prev=True)

        dd = stock.get_market_cap_by_ticker(open_fromDate)
        dd = dd.sort_values(by='시가총액', ascending=True)

        kospi_list = stock.get_market_ticker_list(open_fromDate, market="KOSPI")
        kosdaq_list = stock.get_market_ticker_list(open_fromDate, market="KOSDAQ")
        
        """
        하위 exclude_number개 제외
        max_number개의 주식으로 portfolio 구성
        """
        exclude_number = 20
        max_number = 50
        search_number = exclude_number + max_number
        if market == "KOSPI":
            small_stock_list = []
            for i in range(len(dd)):
                if dd.index[i] in kospi_list:
                    small_stock_list.append(dd.index[i])
                    if len(small_stock_list) == search_number:
                        break
        elif market == "KOSDAQ":
            small_stock_list = []
            for i in range(len(dd)):
                if dd.index[i] in kosdaq_list:
                    small_stock_list.append(dd.index[i])
                    if len(small_stock_list) == search_number:
                        break
        elif market == "MIX":
            small_stock_list = []
            for i in range(len(dd)):
                if dd.index[i] in kospi_list or dd.index[i] in kosdaq_list:
                    small_stock_list.append(dd.index[i])
                    if len(small_stock_list) == search_number:
                        break
        else:
            print("INVALID MARKET")
            return

        small_stock_list = small_stock_list[exclude_number:]

        code_list = []
        buy_price = []
        sell_price = []
        yield_list = []

        for i in range(len(small_stock_list)):
            # 거래 시작일에 거래 정지였던 종목 배제
            db = stock.get_market_ohlcv_by_date(open_fromDate, open_fromDate, small_stock_list[i])
            if db.iloc[0]['시가'] == 0:
                continue

            code_list.append(small_stock_list[i])
            buy_price.append(db.iloc[0]['종가'])

            ds = stock.get_market_ohlcv_by_date(open_toDate, open_toDate, small_stock_list[i])

            if ds.empty:
                with pd.option_context('display.max_rows', None, 'display.max_columns', None):
                    # print(stock.get_market_ohlcv_by_date(open_fromDate, open_toDate, lowPBR_list[i]))
                    dx = stock.get_market_ohlcv_by_date(open_fromDate, open_toDate, small_stock_list[i])
                    sell_price.append(dx[dx['시가'] > 0].iloc[-1]['종가'])
            else:
                sell_price.append(ds.iloc[0]['종가'])

        for i in range(len(buy_price)):
            yield_list.append((sell_price[i] - buy_price[i]) / buy_price[i] + 1)

        term_list.append(open_fromDate + '~' + open_toDate)
        profit_list.append(round(np.mean(yield_list), 4))
        print('기간: ' + open_fromDate + '~' + open_toDate)
        print(round(np.mean(yield_list), 4))

        this_fromDate = this_toDate
        this_toDate = datetime.strftime(datetime.strptime(this_fromDate, "%Y%m%d")
                                    + timedelta(days=duration), "%Y%m%d")
        count = count + 1

        if datetime.strptime(this_toDate, "%Y%m%d").date() > datetime.now().date():
            break

    data = {'기간': term_list, '수익률': profit_list}
    df = pd.DataFrame(data=data)
    file_name = './smallStock_backTesting_' + market + '.xlsx'
    writer = pd.ExcelWriter(file_name, engine='xlsxwriter')
    df.to_excel(writer)
    writer.close()


smallStock_backTesting(market="KOSPI", start_year="2010", start_month="11", period="half year")
smallStock_backTesting(market="KOSDAQ", start_year="2010", start_month="11", period="half year")
smallStock_backTesting(market="MIX", start_year="2010", start_month="11", period="half year")

