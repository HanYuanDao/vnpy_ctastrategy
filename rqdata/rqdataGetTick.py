import rqdatac as rq

rq.init(13971447255, 'hzlianhd520')

df = rq.get_price('J2109', start_date='20210820', end_date='20210822', frequency='tick', expect_df=False)

for row in df.itertuples():
    print(row)