

import pandas as pd
import OpenDartReader
import csv
import openpyxl


def debt_ratio(code: str, year: str):
    """
    :param code: company code
    :param year: fiscal year
    :return: 자본, 부채, 부채 비율
    """
    api_key = '******************************'
    dart = OpenDartReader(api_key)
    df = dart.finstate(code, year)
    if df is None or df.empty:
        return 9999
    fs_cfs = df[df['fs_div'].str.contains('CFS')]
    if fs_cfs.empty:
        return 9999
    fs_bs = fs_cfs[fs_cfs['sj_div'].str.contains('BS')]
    fs_equity = fs_bs[fs_bs['account_nm'].str.contains('자본총계')]
    fs_debt = fs_bs[fs_bs['account_nm'].str.contains('부채총계')]
    equity = fs_equity[['thstrm_amount']].iloc[0, 0].replace(',', '').strip()
    debt = fs_debt[['thstrm_amount']].iloc[0, 0].replace(',', '').strip()
    return int(debt) / int(equity)


a = debt_ratio('005930', '2013')
print(a)

# with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
#     print('a')



