from collections import namedtuple

# 定义每次请求的实时交易数据结构体
RealTimeQuote = namedtuple("RealTimeQuote", (
    "code",  # 股票代码
    "name",  # 股票名称
    "today_opening_price",  # 今日开盘价
    "yesterday_closing_price",  # 昨日收盘价
    "current_price",  # 当前价格
    "today_max_price",  # 今日最高价
    "today_min_price",  # 今日最低价
    "max_buy_price",  # 竞买价，即当前买方最高价、买一出价
    "min_sell_price",  # 竞卖价，即当前卖放最低价、卖一报价
    "shares_of_traded",  # 交易股数
    "amount_of_traded",  # 交易金额（元）
    "buy_one_apply",  # 买一申请购入股数
    "buy_one_price",  # 买一出价
    "buy_two_apply",  # 以下为买二至买五
    "buy_two_price",
    "buy_three_apply",
    "buy_three_price",
    "buy_four_apply",
    "buy_four_price",
    "buy_five_apply",
    "buy_five_price",
    "sell_one_apply",  # 卖一出售股数
    "sell_one_price",  # 卖一报价
    "sell_two_apply",  # 以下为卖二至卖五
    "sell_two_price",
    "sell_three_apply",
    "sell_three_price",
    "sell_four_apply",
    "sell_four_price",
    "sell_five_apply",
    "sell_five_price",
    "date",  # 日期：yyyy-mm-dd
    "time",  # 时间：hh:mm:ss
))

# 定义股票基础信息结构体
Stock = namedtuple("Stock", (
    "code",  # 股票代码
    "name",  # 股票名称
    "net_profit",  # 净利润
    "total_market_value",  # 总市值
    "circulating_market_value",  # 流通市值
    "trade",  # 所处行业
    "PER",  # 市盈率
    "PBR",  # 市净率
    "ROE",  # 净资产收益率
    "gross_margin",  # 毛利率
    "net_margin",  # 净利率
    "bk_code",  # 板块编号
))
