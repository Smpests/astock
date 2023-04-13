from datetime import datetime

# 需要过滤掉的退市股、ST股、新股
BAD_STOCK_NAME_CONTAINS = ["退", "ST", "N"]
# 上交所股票代码开头
SHANGHAI_PREFIX = ("600", "601", "603", "605", "688", "900")
# 北交所股票代码开头
BEIJING_PREFIX = ("8", "43")
# 上半场开盘时间
FIRST_OPENING_TIME = datetime.strptime("9:30", "%H:%M").time()
# 上半场收盘时间
FIRST_CLOSING_TIME = datetime.strptime("11:30", "%H:%M").time()
# 下半场开盘时间
SECOND_OPENING_TIME = datetime.strptime("13:00", "%H:%M").time()
# 下半场收盘时间
SECOND_CLOSING_TIME = datetime.strptime("15:00", "%H:%M").time()
