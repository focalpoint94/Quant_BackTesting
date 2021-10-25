
# SuperTrend.py

import pandas as pd

from pykrx import stock

import matplotlib.pyplot as plt
import matplotlib.font_manager as plt_fm
import matplotlib.dates as mdates

from mpl_finance import candlestick_ohlc

import os

import numpy as np


font_path = "./font/godoFont_all/godoMaum.ttf"
font_prop = plt_fm.FontProperties(fname=font_path, size=18)


def calc_MDD(df, start_idx, end_idx):
    """
    :param df: dataframe
    :param start_idx: dataframe의 시작 idx
    :param end_idx: dataframe의 종료 idx
    :return: MDD
    """
    high = df.iloc[start_idx]['고가']
    low = df.iloc[start_idx]['저가']
    MDD = 0
    for i in range(start_idx + 1, end_idx + 1):
        # 신고가 갱신
        if df.iloc[i]['고가'] > high:
            high = df.iloc[i]['고가']
            low = df.iloc[i]['저가']
        else:
            low = min(low, df.iloc[i]['저가'])
            if low != 0:
                MDD = max(MDD, (high - low) / high * 100)
    return MDD


def supertrend(fromDate, toDate, code, isStock=True, Period=10, Multiplier=3, stop_loss=0.05):
    """
    :param fromDate: backTesting 시작일
    :param toDate: backTesting 종료일
    :param code: 주식 코드 (type = str)
    :param isStock: 주식 or ETF 여부
    :param Period: supertrend의 period
    :param Multiplier: supertrend의 multiplier
    :param stop_loss: 손절매 기준 수익률(e.g. stop_loss=0.05 -> -5% 도달 시 손절)
    :return: code, name, 전략 수익률, 전략 수익률(세금 O), 종목 수익률, 전략 MDD, 종목 MDD
    """
    """
    Data
    """
    if isStock:
        df = stock.get_market_ohlcv_by_date(fromDate, toDate, code)
        name = stock.get_market_ticker_name(code)
    else:
        df = stock.get_index_ohlcv_by_date(fromDate, toDate, code)
        name = stock.get_index_ticker_name(code)
    df['날짜'] = df.index.map(mdates.date2num)
    ohlc = df[['날짜', '시가', '고가', '저가', '종가']]

    """
    Data 부족
    """
    if len(df) < 100:
        return None, None, None, None, None, None, None

    """
    TR
    """
    TR_list = []
    TR_list.append(df.iloc[0]['고가'] - df.iloc[0]['저가'])
    for i in range(1, len(df)):
        opt1 = df.iloc[i]['고가'] - df.iloc[i]['저가']
        opt2 = df.iloc[i]['고가'] - df.iloc[i-1]['종가']
        opt3 = df.iloc[i]['저가'] - df.iloc[i-1]['종가']
        TR = max(opt1, opt2, opt3, 1)
        TR_list.append(TR)
    df.insert(len(df.columns), 'TR', TR_list)

    """
    ATR
    """
    ATR_list = []
    ATR_list.append(TR_list[0])
    for i in range(1, len(df)):
        ATR = (df.iloc[i-1]['TR']*(Period - 1) + df.iloc[i]['TR']) / Period
        ATR_list.append(ATR)
    df.insert(len(df.columns), 'ATR', ATR_list)

    """
    Basic Upper Band
    """
    BUB_list = []
    for i in range(len(df)):
        BUB = (df.iloc[i]['고가'] + df.iloc[i]['저가']) / 2 + Multiplier * df.iloc[i]['TR']
        BUB_list.append(BUB)
    df.insert(len(df.columns), 'Basic Upper Band', BUB_list)

    """
    Basic Lower Band
    """
    BLB_list = []
    for i in range(len(df)):
        BLB = (df.iloc[i]['고가'] + df.iloc[i]['저가']) / 2 - Multiplier * df.iloc[i]['TR']
        BLB_list.append(BLB)
    df.insert(len(df.columns), 'Basic Lower Band', BLB_list)

    """
    Final Upper Band
    """
    FUB_list = [0, ]
    for i in range(1, len(df)):
        opt1 = df.iloc[i]['Basic Upper Band']
        opt2 = FUB_list[i-1]
        FUB = opt1 if df.iloc[i]['Basic Upper Band'] < FUB_list[i-1] or \
            df.iloc[i-1]['종가'] > FUB_list[i-1] else opt2
        FUB_list.append(FUB)
    df.insert(len(df.columns), 'Final Upper Band', FUB_list)

    """
    Final Lower Band
    """
    FLB_list = [0, ]
    for i in range(1, len(df)):
        opt1 = df.iloc[i]['Basic Lower Band']
        opt2 = FLB_list[i-1]
        FLB = opt1 if df.iloc[i]['Basic Lower Band'] > FLB_list[i-1] or \
            df.iloc[i-1]['종가'] < FLB_list[i-1] else opt2
        FLB_list.append(FLB)
    df.insert(len(df.columns), 'Final Lower Band', FLB_list)

    """
    Super Trend
    """
    ST_list = [0, ]
    buy_signal_list = []
    sell_signal_list = []
    for i in range(1, len(df)-1):
        if ST_list[i-1] == df.iloc[i-1]['Final Upper Band'] and \
            df.iloc[i]['종가'] <= df.iloc[i]['Final Upper Band']:
            ST = df.iloc[i]['Final Upper Band']
        elif ST_list[i-1] == df.iloc[i-1]['Final Upper Band'] and \
            df.iloc[i]['종가'] > df.iloc[i]['Final Upper Band']:
            ST = df.iloc[i]['Final Lower Band']
            buy_signal_list.append(i)
        elif ST_list[i-1] == df.iloc[i-1]['Final Lower Band'] and \
            df.iloc[i]['종가'] >= df.iloc[i]['Final Lower Band']:
            ST = df.iloc[i]['Final Lower Band']
        elif ST_list[i-1] == df.iloc[i-1]['Final Lower Band'] and \
            df.iloc[i]['종가'] < df.iloc[i]['Final Lower Band']:
            ST = df.iloc[i]['Final Upper Band']
            sell_signal_list.append(i)
        ST_list.append(ST)
    ST_list.append(ST_list[-1])
    df.insert(len(df.columns), 'Super Trend', ST_list)

    """
    Debug
    """
    # writer = pd.ExcelWriter('./debug.xlsx', engine='xlsxwriter')
    # df.to_excel(writer)
    # writer.close()
    # for buy in buy_signal_list:
    #     print(df.index[buy])
    # for sell in sell_signal_list:
    #     print(df.index[sell])

    """
    전략 수익률
    """
    profit = 1
    profit_with_tax = 1
    tax_rate = 0.00315 if isStock else 0.00015
    # Buy Singal 및 Sell Signal이 없는 경우
    if not buy_signal_list or not sell_signal_list:
        pass
    else:
        # 1. Buy Signal이 Sell Signal을 선행하는 경우
        # 1-1 Buy Signal이 1회 더 많은 경우: 마지막 Buy Signal 무시
        if buy_signal_list[0] < sell_signal_list[0] and \
            len(buy_signal_list) > len(sell_signal_list):
            for i in range(len(buy_signal_list) - 1):
                buy_price = df.iloc[buy_signal_list[i]+1]['시가']
                if buy_price == 0:
                    continue
                sell_price = df.iloc[sell_signal_list[i]+1]['시가']
                delta = (sell_price - buy_price) / buy_price
                if delta < -stop_loss:
                    delta = -stop_loss
                profit = profit * (1 + delta)
                delta_with_tax = ((1 - tax_rate) * sell_price - (1 + tax_rate) * buy_price) / buy_price
                if delta_with_tax < -stop_loss:
                    delta_with_tax = -stop_loss
                profit_with_tax = profit_with_tax * (1 + delta_with_tax)
        # 1-2 Buy Signal 수 = Sell Signal 수
        elif buy_signal_list[0] < sell_signal_list[0] and \
            len(buy_signal_list) == len(sell_signal_list):
            for i in range(len(buy_signal_list)):
                buy_price = df.iloc[buy_signal_list[i]+1]['시가']
                if buy_price == 0:
                    continue
                sell_price = df.iloc[sell_signal_list[i]+1]['시가']
                delta = (sell_price - buy_price) / buy_price
                if delta < -stop_loss:
                    delta = -stop_loss
                profit = profit * (1 + delta)
                delta_with_tax = ((1 - tax_rate) * sell_price - (1 + tax_rate) * buy_price) / buy_price
                if delta_with_tax < -stop_loss:
                    delta_with_tax = -stop_loss
                profit_with_tax = profit_with_tax * (1 + delta_with_tax)
        # 2. Sell Signal이 Buy Signal을 선행하는 경우
        # 2-1 Sell Signal이 1회 더 많은 경우: 첫 Sell Signal 무시
        elif sell_signal_list[0] > buy_signal_list[0] and \
            len(sell_signal_list) > len(buy_signal_list):
            for i in range(1, len(sell_signal_list)):
                buy_price = df.iloc[buy_signal_list[i-1]+1]['시가']
                if buy_price == 0:
                    continue
                sell_price = df.iloc[sell_signal_list[i]+1]['시가']
                delta = (sell_price - buy_price) / buy_price
                if delta < -stop_loss:
                    delta = -stop_loss
                profit = profit * (1 + delta)
                delta_with_tax = ((1 - tax_rate) * sell_price - (1 + tax_rate) * buy_price) / buy_price
                if delta_with_tax < -stop_loss:
                    delta_with_tax = -stop_loss
                profit_with_tax = profit_with_tax * (1 + delta_with_tax)
        # 2-2 Buy Signal 수 = Sell Signal 수
        elif sell_signal_list[0] > buy_signal_list[0] and \
            len(buy_signal_list) == len(sell_signal_list):
            for i in range(1, len(sell_signal_list)):
                buy_price = df.iloc[buy_signal_list[i-1]+1]['시가']
                if buy_price == 0:
                    continue
                sell_price = df.iloc[sell_signal_list[i]+1]['시가']
                delta = (sell_price - buy_price) / buy_price
                if delta < -stop_loss:
                    delta = -stop_loss
                profit = profit * (1 + delta)
                delta_with_tax = ((1 - tax_rate) * sell_price - (1 + tax_rate) * buy_price) / buy_price
                if delta_with_tax < -stop_loss:
                    delta_with_tax = -stop_loss
                profit_with_tax = profit_with_tax * (1 + delta_with_tax)
        else:
            print("수익률 계산 오류")
            return

    """
    기타 수익률 (개별 종목 수익률 / 코스피 수익률)
    """
    kospi_df = stock.get_index_ohlcv_by_date(fromDate, toDate, "1001")
    profit_without_strat = ((1 - tax_rate) * df.iloc[-1]['종가'] - (1 + tax_rate) * df.iloc[0]['시가']) \
                           / df.iloc[0]['시가'] + 1
    profit_of_kospi = ((1 - tax_rate) * kospi_df.iloc[-1]['종가'] - (1 + tax_rate) * kospi_df.iloc[0]['시가']) \
                           / kospi_df.iloc[0]['시가'] + 1

    """
    전략 MDD
    """
    MDD_strat = 0
    # Buy Singal 및 Sell Signal이 없는 경우
    if not buy_signal_list or not sell_signal_list:
        pass
    else:
        # 1. Buy Signal이 Sell Signal을 선행하는 경우
        # 1-1 Buy Signal이 1회 더 많은 경우: 마지막 Buy Signal 무시
        if buy_signal_list[0] < sell_signal_list[0] and \
                len(buy_signal_list) > len(sell_signal_list):
            for i in range(len(buy_signal_list) - 1):
                MDD_strat = max(MDD_strat, calc_MDD(df, buy_signal_list[i]+1, sell_signal_list[i]))
        # 1-2 Buy Signal 수 = Sell Signal 수
        elif buy_signal_list[0] < sell_signal_list[0] and \
                len(buy_signal_list) == len(sell_signal_list):
            for i in range(len(buy_signal_list)):
                MDD_strat = max(MDD_strat, calc_MDD(df, buy_signal_list[i]+1, sell_signal_list[i]))
        # 2. Sell Signal이 Buy Signal을 선행하는 경우
        # 2-1 Sell Signal이 1회 더 많은 경우: 첫 Sell Signal 무시
        elif sell_signal_list[0] > buy_signal_list[0] and \
                len(sell_signal_list) > len(buy_signal_list):
            for i in range(1, len(sell_signal_list)):
                MDD_strat = max(MDD_strat, calc_MDD(df, buy_signal_list[i-1]+1, sell_signal_list[i]))
        # 2-2 Buy Signal 수 = Sell Signal 수
        elif sell_signal_list[0] > buy_signal_list[0] and \
                len(buy_signal_list) == len(sell_signal_list):
            for i in range(1, len(sell_signal_list)):
                MDD_strat = max(MDD_strat, calc_MDD(df, buy_signal_list[i-1]+1, sell_signal_list[i]))
        else:
            print("MDD 계산 오류")
            return

    """
    기타 MDD (개별 종목 수익률 / 코스피 수익률)
    """
    MDD_without_strat = calc_MDD(df, 0, len(df)-1)
    MDD_of_kospi = calc_MDD(kospi_df, 0, len(kospi_df)-1)

    """
    Plot
    """
    if not os.path.isdir('./supertrend_graphs'):
        os.mkdir('./supertrend_graphs')
    plot_title = name + ' (Ticker: ' + str(code) + ')'
    plot_text = '전략 수익률: ' + str(round(profit, 4)) + '\n' \
        + '전략 수익률(세금 O): ' + str(round(profit_with_tax, 4)) + '\n' \
        + '종목 수익률: ' + str(round(profit_without_strat, 4)) + '\n' \
        + '시장 수익률: ' + str(round(profit_of_kospi, 4)) + '\n' \
        + '전략 MDD: ' + str(round(MDD_strat, 2)) + '\n' \
        + '종목 MDD: ' + str(round(MDD_without_strat, 2)) + '\n' \
        + '시장 MDD: ' + str(round(MDD_of_kospi, 2)) + '\n' \

    figure1 = plt.figure(1, figsize=(9, 9))
    p1 = figure1.add_subplot()
    p1.text(df.날짜[-200], 0.9 * df.종가.min(), plot_text, style='italic',
            bbox={'facecolor': 'white', 'alpha': 0.5, 'pad': 10})
    plt.title(plot_title, fontproperties=font_prop)
    plt.grid(True)
    candlestick_ohlc(p1, ohlc.values[1:], width=.6, colorup='red', colordown='blue')
    plt.plot(df.날짜[1:], df['Super Trend'][1:], label='Super Trend')
    p1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    for buy_signal in buy_signal_list:
        day = df.iloc[buy_signal]['날짜']
        plt.vlines(day, 0.9 * df.종가.min(), 1.1 * df.종가.max(), colors='red', linewidth=1)
    for sell_signal in sell_signal_list:
        day = df.iloc[sell_signal]['날짜']
        plt.vlines(day, 0.9 * df.종가.min(), 1.1 * df.종가.max(), colors='green', linewidth=1)
    plt.legend(loc='best')
    figure1.savefig(fname='./supertrend_graphs/' + code, dpi=300)
    plt.close()
    # plt.show()
    return code, name, round(profit, 4), round(profit_with_tax, 4), round(profit_without_strat, 4), \
        round(MDD_strat, 2), round(MDD_without_strat, 2)


def supertrend_backTester(fromDate, toDate, code_list, isStock=True, Period=10, Multiplier=3, stop_loss=0.05):
    df_code_list = []
    name_list = []
    profit_list = []
    profit_with_tax_list = []
    profit_without_strat_list = []
    MDD_strat_list = []
    MDD_without_strat_list = []
    for i in range(len(code_list)):
        code, name, profit, profit_with_tax, profit_without_strat, MDD_strat, MDD_without_strat = \
            supertrend(fromDate, toDate, code_list[i], isStock, Period, Multiplier, stop_loss)
        if code == None: continue
        df_code_list.append(code)
        name_list.append(name)
        profit_list.append(profit)
        profit_with_tax_list.append(profit_with_tax)
        profit_without_strat_list.append(profit_without_strat)
        MDD_strat_list.append(MDD_strat)
        MDD_without_strat_list.append(MDD_without_strat)
    profit_avg = np.mean(profit_list)
    profit_with_tax_avg = np.mean(profit_with_tax_list)
    profit_without_strat_avg = np.mean(profit_without_strat_list)
    MDD_strat_avg = np.mean(MDD_strat_list)
    MDD_without_strat_avg = np.mean(MDD_without_strat_list)
    return profit_avg, profit_with_tax_avg, profit_without_strat_avg, MDD_strat_avg, MDD_without_strat_avg



"""
Test Params
"""
fromDate = "20100101"
toDate = "20210430"
# code = "000270"
isStock = True

"""
Super Trend Params
"""
Period = 10
Multiplier = 3
stop_loss = 0.05

"""
종목 선정
"""
temp = stock.get_market_cap_by_ticker(fromDate)
past_list = list(temp.index[:100])
temp = stock.get_market_ticker_list(toDate)
code_list = [x for x in past_list if x in temp]

"""
BackTest
"""
profit_avg, profit_with_tax_avg, profit_without_strat_avg, MDD_strat_avg, MDD_without_strat_avg = supertrend_backTester(fromDate, toDate, code_list, isStock, Period, Multiplier, stop_loss)

print("<2010년 01월 - 2021년 04월, KOSPI 시총 상위 100 기업> SuperTrend 지표 투자 결과")
print(
    f'전략 수익률: {profit_avg:.4f}'
    f'전략 수익률(세금 O): {profit_with_tax_avg:.4f}'
    f'종목 수익률: {profit_without_strat_avg:.4f}'
    f'전략 MDD: {MDD_strat_avg:.4f}'
    f'종목 MDD: {MDD_without_strat_avg:.4f}'
)

