import os


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCES_DIR = os.path.join(ROOT_DIR, "test_resource")
# RESOURCES_DIR = os.path.join(ROOT_DIR, "resources")

STOCK_BASIC_INFO_CACHE_PATH = os.path.join(RESOURCES_DIR, "stock_basic.csv")
SINA_REAL_TIME_QUOTE_API = "https://hq.sinajs.cn/list={codes}"  # example: https://hq.sinajs.cn/list=sz001,sh110
SINA_REAL_TIME_QUOTE_API_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
    "Referer": "https://finance.sina.com.cn",
}
