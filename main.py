import signal
import time
from typing import List
import efinance as ef
import multitasking
import pandas as pd
from retry import retry
from schedule import repeat, every, run_pending, Job
from tqdm import tqdm

import config
import os
import requests

from decorator import cost
from stock import Stock, RealTimeQuote
from utils import parse_sina_response_text, df_to_csv, code_with_prefix, is_bad_stock, is_trade_time

# kill all tasks on ctrl-c
signal.signal(signal.SIGINT, multitasking.killall)
multitasking.set_max_threads(10)


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
        """
        :param update: 是否更新基础股票信息数据（主要用到股票代码，没必要频繁更新）
        """
        if update or not os.path.exists(config.STOCK_BASIC_INFO_CACHE_PATH):
            stock_basic_info = ef.stock.get_base_info(ef.stock.get_realtime_quotes()["股票代码"])
            stock_basic_info.dropna(subset=["流通市值"], inplace=True)
            stock_basic_info.to_csv(config.STOCK_BASIC_INFO_CACHE_PATH, index=False, encoding="utf-8")
        stock_basic_info = pd.read_csv(config.STOCK_BASIC_INFO_CACHE_PATH, encoding="utf-8")
        stock_basic_info.dropna(subset=["流通市值"], inplace=True)
        self.stocks = dict()
        self.stocks_code = list()
        self.real_time_df_dict = dict()
        for row in stock_basic_info.itertuples(index=False):
            if is_bad_stock(row[1]):
                continue
            code = code_with_prefix(str(row[0]))
            self.stocks[code] = Stock(*row)  # *解包数组、元组，**解包字典
            self.stocks_code.append(code)
        self.session = requests.Session()
        self.session.headers.update(config.SINA_REAL_TIME_QUOTE_API_HEADERS)
        self.stocks_count = len(self.stocks_code)
        self.schedule_task_finished = True
        # TODO: 从文件中加载当天的历史数据

    @retry(tries=3, delay=1)
    def get_real_time_quotes(self, stock_codes: List[str]) -> str:
        try:
            response = self.session.get(
                url=config.SINA_REAL_TIME_QUOTE_API.format(codes=",".join(stock_codes)),
                timeout=3,
            )
            if response.status_code != 200:
                raise ValueError("Wrong status code")
            if "FAILED" in response.text:
                raise ValueError("Wrong text")
            return response.text
        except Exception:
            raise

    @cost
    def update_real_time_quotes(self, batch_size=200):
        progress_bar = tqdm(range(0, self.stocks_count, batch_size))
        for epoch in range(0, self.stocks_count, batch_size):
            self.batch_update_real_time_quotes(self.stocks_code[epoch:epoch + batch_size], progress_bar)
        # 等待所有线程执行完毕
        multitasking.wait_for_tasks()

    @multitasking.task
    def batch_update_real_time_quotes(self, stock_codes: List[str], progress_bar: tqdm):
        response = self.get_real_time_quotes(stock_codes)
        self._parse_and_update(response)
        progress_bar.update(1)
        progress_bar.set_description("fetch real time data")

    def _save_to_df_and_file(self, real_time_quote: RealTimeQuote):
        new_row = pd.DataFrame([real_time_quote])
        if real_time_quote.code in self.real_time_df_dict:
            self.real_time_df_dict[real_time_quote.code].append(new_row)
        else:
            self.real_time_df_dict[real_time_quote.code] = new_row
        df_to_csv(new_row)

    def _parse_and_update(self, response: str):
        stock_texts = response.split("\n")
        for text in stock_texts:
            real_time_quote = parse_sina_response_text(text)
            if real_time_quote:
                self._save_to_df_and_file(real_time_quote)

    def __load_today_quote_history(self):
        pass


stock_manager = StockManager()

while True:
    # todo: 或许time.sleep(seconds)可以是动态的，在交易时间内是20s，交易时间外要等待直到下一个交易时间
    if is_trade_time():
        stock_manager.update_real_time_quotes()
    else:
        print("It's not trading time now")
    time.sleep(20)
