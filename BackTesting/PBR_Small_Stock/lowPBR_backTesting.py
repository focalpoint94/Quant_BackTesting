
from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

"""
market: "KOSPI" "KOSDAQ" "MIX"
start_year: 투자 시작 연도 ('2014' ;str)
start_month: 투자 시작 월 ('11', ;str)
period: 'year', 'half year', 'quarter', 'month' ;str
"""
def lowPBR_backTesting(market: str='KOSPI', start_year: str='2014', start_month: str='11', period: str='half year'):
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
        if market == "KOSPI" or market == "KOSDAQ":
            df = stock.get_market_fundamental_by_ticker(open_fromDate, market=market)
            df = df.sort_values(by='PBR', ascending=True)
            df = df[df['PBR'] > 0.2]
            lowPBR_list = df.index[:50]
        elif market == "MIX":
            df = stock.get_market_fundamental_by_ticker(open_fromDate, market="KOSPI")
            df = df.sort_values(by='PBR', ascending=True)
            df = df[df['PBR'] > 0.2]
            temp1 = df.index[:25].to_list()
            df = stock.get_market_fundamental_by_ticker(open_fromDate, market="KOSDAQ")
            df = df.sort_values(by='PBR', ascending=True)
            df = df[df['PBR'] > 0.2]
            temp2 = df.index[:25].to_list()
            lowPBR_list = temp1 + temp2
        else:
            print("INVALID MARKET")
            return

        code_list = []
        buy_price = []
        sell_price = []
        yield_list = []

        for i in range(len(lowPBR_list)):
            # 거래 시작일에 거래 정지였던 종목 배제
            db = stock.get_market_ohlcv_by_date(open_fromDate, open_fromDate, lowPBR_list[i])
            if db.iloc[0]['시가'] == 0:
                continue

            code_list.append(lowPBR_list[i])
            buy_price.append(db.iloc[0]['종가'])

            ds = stock.get_market_ohlcv_by_date(open_toDate, open_toDate, lowPBR_list[i])
            # print(lowPBR_list[i])
            # print(ds)
            if ds.empty:
                with pd.option_context('display.max_rows', None, 'display.max_columns', None):
                    # print(stock.get_market_ohlcv_by_date(open_fromDate, open_toDate, lowPBR_list[i]))
                    dx = stock.get_market_ohlcv_by_date(open_fromDate, open_toDate, lowPBR_list[i])
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
    file_name = './lowPBR_backTesting_' + market + '.xlsx'
    writer = pd.ExcelWriter(file_name, engine='xlsxwriter')
    df.to_excel(writer)
    writer.close()

lowPBR_backTesting(market="KOSPI", start_year="2011", start_month="01", period="half year")

