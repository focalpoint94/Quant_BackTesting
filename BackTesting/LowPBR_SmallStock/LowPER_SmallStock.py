
"""
LowPER_SmallStock.py
LowPER + 소형주 전략의 BackTesting
"""
from pykrx import stock
import pandas as pd
from datetime import datetime
from time import sleep
import numpy as np
import math


"""
Functions
"""
def calc_yield(**args):
    """
    :param args: dictionary
    <keys>
    test_year = "2010"
    test_month = "11"
    PER_upper_threshold = 5
    PER_lower_threshold = 0.3
    num_stock_limit = 30
    upper_yield_limit = 50
    lower_yield_limit = 30
    duration = 1 (year)
    duration = 1 (year)

    :return: 평균 수익률, 동기간 코스피 수익률
    """
    test_year = args['test_year']
    test_month = args['test_month']
    PER_upper_threshold = args['PER_upper_threshold']
    PER_lower_threshold = args['PER_lower_threshold']
    num_stock_limit = args['num_stock_limit']
    upper_yield_limit = args['upper_yield_limit']
    lower_yield_limit = args['lower_yield_limit']
    duration = args['duration']  # duration unit: year

    tax_rate = 0.00315
    test_date = test_year + test_month + "01"
    test_end_date = min(str(int(test_year) + duration) + test_month + "01",
                        datetime.strftime(datetime.now().date(), "%Y%m%d"))
    test_date = stock.get_nearest_business_day_in_a_week(date=test_date, prev=False)
    test_end_date = stock.get_nearest_business_day_in_a_week(date=test_end_date, prev=True)

    """
    Loading Data
    """
    df1 = stock.get_market_fundamental_by_ticker(test_date, market="KOSPI")
    df2 = stock.get_market_fundamental_by_ticker(test_date, market="KOSDAQ")
    df = pd.concat([df1, df2])
    df = df[(df['PER'] < PER_upper_threshold) & (df['PER'] > PER_lower_threshold)]
    df = df.sort_values(by='PER', ascending=True)
    df = df[['PER']]
    code_list = df.index.to_list()
    lowPER_smallstock_list = []
    temp = stock.get_market_cap_by_ticker(test_date)
    temp = temp[['시가총액']]
    temp = temp.sort_values(by='시가총액', ascending=True)
    smallstock_list = temp.index.to_list()[:len(temp) // 5]
    PER_list = []
    for code in code_list:
        if code in smallstock_list:
            lowPER_smallstock_list.append(code)
            PER_list.append(df.loc[code]['PER'])

    """
    lowPER_smallstock_list: The Basket
    PER_list: PER 값
    name_list: 종목명
    buy_price: 매수 가격
    sell_price: 매도 가격

    매수: Test Date 시가 매수
    익절 조건: 상한 수익률 돌파 시
    손절 조건: 하한 수익률 돌파 시
    매도 조건: duration 기간 말
    """
    lowPER_smallstock_list = lowPER_smallstock_list[:num_stock_limit]
    PER_list = PER_list[:num_stock_limit]
    name_list = []
    buy_price = []
    sell_price = []
    yield_list = []

    for code in lowPER_smallstock_list:
        name = stock.get_market_ticker_name(code)
        name_list.append(name)
        temp = stock.get_market_ohlcv_by_date(test_date, test_date, code)
        bought_price = temp.iloc[0]['시가']
        buy_price.append(bought_price)
        sleep(1)

    """
    수익률 계산
    """
    for i, code in enumerate(lowPER_smallstock_list):
        df = stock.get_market_ohlcv_by_date(test_date, test_end_date, code)
        upper_target_price = buy_price[i] * (1 + upper_yield_limit / 100)
        lower_target_price = buy_price[i] * (1 - lower_yield_limit / 100)
        sold = False
        for j in range(len(df)):
            if df.iloc[j]['저가'] <= upper_target_price <= df.iloc[j]['고가']:
                sold_price = upper_target_price
                sell_price.append(sold_price)
                sold = True
                break
            if df.iloc[j]['저가'] <= lower_target_price <= df.iloc[j]['고가']:
                sold_price = lower_target_price
                sell_price.append(sold_price)
                sold = True
                break
        if not sold:
            sold_price = df.iloc[-1]['종가']
            sell_price.append(sold_price)
        sleep(1)

    for i, code in enumerate(lowPER_smallstock_list):
        # 매수 시점 거래 정지 종목 제외
        if buy_price[i] == 0:
            yield_list.append(math.nan)
            continue
        yield_with_tax = ((1 - tax_rate) * sell_price[i] - (1 + tax_rate) * buy_price[i]) / buy_price[i] + 1
        yield_list.append(round(yield_with_tax, 4))

    """
    NAN Check
    """
    _yield_list = [_yield for _yield in yield_list if not math.isnan(_yield)]

    kospi = stock.get_index_ohlcv_by_date(test_date, test_end_date, "1001")
    kospi_yield = (kospi.iloc[-1]['종가'] - kospi.iloc[0]['시가']) / kospi.iloc[0]['시가'] + 1

    print("* Low PER 소형주 전략")
    print("* 기간: ", test_date + ' ~ ' + test_end_date)
    print("* 종목: ", lowPER_smallstock_list)
    print("* 종목명: ", name_list)
    print("* PER: ", PER_list)
    print("* 종목 수익률: ", yield_list)
    print("* 평균 수익률: ", round(np.mean(_yield_list), 4))
    print("* 동기간 코스피 수익률: ", round(kospi_yield, 4))

    return round(np.mean(_yield_list), 4), round(kospi_yield, 4)


"""
Hyper Params
"""
start_year = 2010
end_year = 2021
PER_upper_threshold = 12
PER_lower_threshold = 5
num_stock_limit = 30
upper_yield_limit = 100
lower_yield_limit = 50
duration = 1 # duration unit: year

"""
Execution
"""
term_list = []
y1_list = []
y2_list = []
for year in range(start_year, end_year + 1):
    test_year = str(year)
    test_month = "01"
    params = dict()
    params['test_year'] = test_year
    params['test_month'] = test_month
    params['PER_upper_threshold'] = PER_upper_threshold
    params['PER_lower_threshold'] = PER_lower_threshold
    params['num_stock_limit'] = num_stock_limit
    params['upper_yield_limit'] = upper_yield_limit
    params['lower_yield_limit'] = lower_yield_limit
    params['duration'] = duration
    term = test_year + '년' + test_month + '월' + ' (최대 보유 기간: ' + str(duration) + '년)'
    y1, y2 = calc_yield(**params)
    term_list.append(term)
    y1_list.append(y1)
    y2_list.append(y2)

data = {'Term': term_list, '전략 수익률': y1_list, '동기간 코스피 수익률': y2_list}
df = pd.DataFrame(data=data)
file_name = './results_PER_' + str(PER_upper_threshold) + '_' + str(PER_lower_threshold) + '_' + str(upper_yield_limit) + '_' + str(lower_yield_limit) + '.xlsx'
writer = pd.ExcelWriter(file_name, engine='xlsxwriter')
df.to_excel(writer)
writer.close()
