
# Quant BackTesting

## LowPBR_LowDebt
- Low PBR/PER 조건과 Low 부채 비율 조건을 동시에 만족하는 주식을 매수하는 알고리즘을 백테스트
- debt_ratio.py: OpenDartReader를 이용하여 부채 비율을 산출하는 예제
- valued_stock_PBR.py: Low PBR + Low Debt Ratio 매수 알고리즘에 대한 백테스트 (HyperParameters: start_year: 투자 시작 연도, end_year: 투자 종료 연됴, PBR_upper_threshold: PBR 상한, PBR_lower_threshold: PBR 하한, debt_ratio_threshold: 부채 비율 상한, num_stock_limit: 최대 매수 종목 수, upper_yield_limit: 익절 수익률, lower_yield_limit: 손절 수익률, duration: 보유 기간(yr))
- valued_stock_PER.py: Low PER + Low Debt Ratio 매수 알고리즘에 대한 백테스트 (HyperParamters: 상기 동일)
- 실행 LOG 예시: 
![image](https://user-images.githubusercontent.com/55021961/138702704-880e54ee-a394-45e1-aba9-418643480631.png)
- 결과 파일 예시:

![image](https://user-images.githubusercontent.com/55021961/138702856-ebed790a-ecb6-48d2-af95-b76106bd79a4.png)


## asdf
