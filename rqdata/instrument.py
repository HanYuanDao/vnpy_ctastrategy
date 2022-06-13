import rqdatac as rq

rq.init(13971447255, 'hzlianhd520')

df = rq.all_instruments(type='Future', market='cn', date=None)

for row in df.itertuples():
    exchange = getattr(row, 'exchange')
    # if exchange == 'CFFEX' or exchange == 'CZCE' or exchange == 'DCE':
    if exchange == 'CFFEX':
        print(getattr(row, 'order_book_id'), getattr(row, 'symbol'))
