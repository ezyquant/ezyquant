from reader import SETDataReader
import datetime
from datetime import date


path = r"C:\Users\User\Desktop\fintech\ezyquant\ssetdi_db.db"
sdr = SETDataReader(path)
datstart = datetime.date(2030, 12, 25)
datend = datetime.date(2030, 12, 30)
print(type(sdr.get_trading_dates(start_date=datstart, end_date=datend)[0]))
# print(sdr.get_trading_dates())
# print(sdr.get_symbol_info(["SET", "BBL"]))
# print(sdr.get_symbol_info())
