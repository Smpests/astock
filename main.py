import signal
from collections import namedtuple
from typing import List, Dict

import efinance as ef
import multitasking
import pandas as pd
from retry import retry
from tqdm import tqdm

import config
import os
import requests

from decorator import cost

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

# kill all tasks on ctrl-c
signal.signal(signal.SIGINT, multitasking.killall)
multitasking.set_max_threads(8)

SHANGHAI_PREFIX = ("600", "601", "603", "605", "688", "900")
BEIJING_PREFIX = ("8", "43")


class SingletonMeta(type):

    def __init__(cls, *args, **kwargs):
        cls.__instance = None
        super().__init__(*args, **kwargs)

    def __call__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__call__(*args, **kwargs)
        return cls.__instance


class StockManager(metaclass=SingletonMeta):
    def __init__(self, update=False):
        if update or not os.path.exists(config.STOCK_BASIC_INFO_CACHE_PATH):
            stock_basic_info = ef.stock.get_base_info(ef.stock.get_realtime_quotes()["股票代码"])
            stock_basic_info.dropna(subset=["流通市值"], inplace=True)
            stock_basic_info.to_csv(config.STOCK_BASIC_INFO_CACHE_PATH, index=False, encoding="utf-8")
        stock_basic_info = pd.read_csv(config.STOCK_BASIC_INFO_CACHE_PATH, encoding="utf-8")
        # TODO: 去除ST股、新股、退市股？
        stock_basic_info.dropna(subset=["流通市值"], inplace=True)
        self.stocks = dict()
        self.stocks_code = list()
        # TODO: 改为util函数处理
        for row in stock_basic_info.itertuples(index=False):
            code = str(row[0]).zfill(6)
            # TODO: 待优化，暂时用于测试
            if "退"in row[1]:
                continue
            if "ST" in row[1]:
                continue
            if "N" in row[1]:
                continue
            if code.startswith(SHANGHAI_PREFIX):
                code = "sh" + code
            elif code.startswith(BEIJING_PREFIX):
                code = "bj" + code
            else:
                code = "sz" + code
            self.stocks[code] = Stock(*row)  # *解包数组、元组，**解包字典
            self.stocks_code.append(code)
        self.session = requests.Session()
        self.session.headers.update(config.SINA_REAL_TIME_QUOTE_API_HEADERS)
        self.stocks_count = len(self.stocks_code)
        # TODO: 从文件中加载当天的历史数据
        self.real_time_df_dict = dict()

    def real_time_batch_request(self, batch_size=500):
        @multitasking.task
        @retry(tries=3, delay=1)
        def get_real_time_quote(stock_codes: List[str]):
            try:
                response = self.session.get(
                    url=config.SINA_REAL_TIME_QUOTE_API.format(codes=",".join(stock_codes)),
                    timeout=3,
                )
                if response.status_code != 200:
                    raise ValueError("Wrong status code")
                if "FAILED" in response.text:
                    raise ValueError("Wrong text")
                real_time_quotes = parse_text_to_object(response.text)
                real_time_data.extend(real_time_quotes)
                progress_bar.update()
                progress_bar.set_description(f"Processing ")
            except Exception:
                raise
        real_time_data = []
        progress_bar = tqdm(range(0, self.stocks_count, batch_size))
        for epoch in range(0, self.stocks_count, batch_size):
            get_real_time_quote(self.stocks_code[epoch:epoch + batch_size])
        # 等待所有线程执行完毕
        multitasking.wait_for_tasks()
        return real_time_data

    def start(self):
        self.update_real_time_quote()

    def update_real_time_quote(self):
        real_time_data = self.real_time_batch_request()
        # 将数据写入df字典
        self.__save_to_df_and_file(real_time_data)

    @cost
    def __save_to_df_and_file(self, real_time_data: List[RealTimeQuote]):
        for _data in real_time_data:
            new_row = pd.DataFrame([_data])
            if _data.code in self.real_time_df_dict:
                self.real_time_df_dict[_data.code].append(new_row)
            else:
                self.real_time_df_dict[_data.code] = new_row
            save_dir = os.path.join(config.RESOURCES_DIR, _data.code)
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            save_path = os.path.join(save_dir, f"{_data.date}.csv")
            new_row.to_csv(
                save_path,
                mode="a",
                index=False,
                encoding="utf-8",
                header=not os.path.exists(save_path)
            )

    def __load_today_quote_history(self):
        pass


def parse_text_to_object(text: str) -> List[RealTimeQuote]:
    real_time_quote_list = []
    stock_texts = text.split("\n")
    for _text in stock_texts:
        _text = _text.strip()
        if not _text:
            continue
        try:
            contains_stock_code, data = _text.split("=")
            stock_code = contains_stock_code[-8:]
            if not stock_code.startswith(("sz", "sh", "bj")):
                print("wrong code")
                continue
            if len(data) > 3:  # 空串至少包含"";三个字符
                real_time_quote = RealTimeQuote(stock_code, *data[1:-1].split(",")[:32])  # 只要33位，后面的暂无意义
                real_time_quote_list.append(real_time_quote)
        except Exception:
            print(f"error text: {_text}")

    return real_time_quote_list


stock_manager = StockManager()
stock_manager.start()
