
"""
NCAV_.py
NCAV 전략의 Backtesting
"""


from pykrx import stock
import pandas as pd
import numpy as np
import json
import math
from datetime import datetime
from time import sleep


def calc_yield(**args):
    """
    :param args: dictionary
    <keys>
    test_year = "2010"
    test_month = "11"
    num_stock_limit = 30
    NCAV_multiple = 1.5
    upper_yield_limit = 50
    lower_yield_limit = 30
    duration = 1 (year)

    :return: 평균 수익률, 동기간 코스피 수익률
    """
    test_year = args['test_year']
    test_month = args['test_month']
    num_stock_limit = args['num_stock_limit']
    NCAV_multiple = args['NCAV_multiple']
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

    temp = stock.get_market_cap_by_ticker(test_date)
    temp = temp[['시가총액']]

    """
    Loading Financial Data
    """
    fiscal_year = str(int(test_year) - 1)
    saved_dir = 'C:/Git/newFinance_workspace/Financial Data/'
    file_name_1 = saved_dir + '유동자산_Data/' + fiscal_year + '.json'
    file_name_2 = saved_dir + '부채총계_Data/' + fiscal_year + '.json'
    file_name_3 = saved_dir + '당기순이익_Data/' + fiscal_year + '.json'
    with open(file_name_1, 'r') as f:
        liquid_asset_list = json.load(f)
    with open(file_name_2, 'r') as f:
        debt_list = json.load(f)
    with open(file_name_3, 'r') as f:
        net_profit_list = json.load(f)

    """
    Stock Basket
    Conditions
    1) 유동자산 - 부채총계 > 시가총액 * NCAV_multiple
    2) 세후이익 > 0
    """
    stock_basket = []
    for code in df.index.to_list():
        liquid_asset = None
        debt = None
        net_profit = None
        for item in liquid_asset_list:
            if item[0] == code:
                liquid_asset = item[1]
                break
        for item in debt_list:
            if item[0] == code:
                debt = item[1]
                break
        for item in net_profit_list:
            if item[0] == code:
                net_profit = item[1]
                break

        if liquid_asset is None or debt is None or net_profit is None or \
                math.isnan(liquid_asset) or math.isnan(debt) or math.isnan(net_profit):
            continue

        if liquid_asset - debt > temp.loc[code]['시가총액'] * NCAV_multiple and net_profit > 0:
            stock_basket.append(code)

    """
    stock_basket: The Basket
    name_list: 종목명
    buy_price: 매수 가격
    sell_price: 매도 가격
    
    매수: Test Date 시가 매수
    익절 조건: 상한 수익률 돌파 시
    손절 조건: 하한 수익률 돌파 시
    매도 조건: duration 기간 말
    """
    if len(stock_basket) > num_stock_limit:
        stock_basket = stock_basket[:num_stock_limit]
    name_list = []
    buy_price = []
    sell_price = []
    yield_list = []

    for code in stock_basket:
        name = stock.get_market_ticker_name(code)
        name_list.append(name)
        temp = stock.get_market_ohlcv_by_date(test_date, test_date, code)
        bought_price = temp.iloc[0]['시가']
        buy_price.append(bought_price)
        sleep(1)

    """
    수익률 계산
    """
    for i, code in enumerate(stock_basket):
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

    for i, code in enumerate(stock_basket):
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

    print("* NCAV 전략")
    print("* 기간: ", test_date + ' ~ ' + test_end_date)
    print("* 종목: ", stock_basket)
    print("* 종목명: ", name_list)
    print("* 종목 수익률: ", yield_list)
    print("* 평균 수익률: ", round(np.mean(_yield_list), 4))
    print("* 동기간 코스피 수익률: ", round(kospi_yield, 4))

    return round(np.mean(_yield_list), 4), round(kospi_yield, 4)



"""
Hyper Params
"""
start_year = 2010
end_year = 2020
num_stock_limit = 30
NCAV_multiple = 1.5
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
    params['num_stock_limit'] = num_stock_limit
    params['NCAV_multiple'] = NCAV_multiple
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
file_name = './results_NCAV_' + str(NCAV_multiple) + '_' + str(upper_yield_limit) + '_' + str(lower_yield_limit) + '.xlsx'
writer = pd.ExcelWriter(file_name, engine='xlsxwriter')
df.to_excel(writer)
writer.close()

