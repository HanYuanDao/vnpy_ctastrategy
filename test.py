import time
import datetime

t = datetime.datetime.now()

mills = int(time.mktime(t.timetuple())) * 1000 + int(t.microsecond / 1000)
print(mills)