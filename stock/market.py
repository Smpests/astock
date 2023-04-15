import asyncio
import os
import signal
import time
from typing import List

import efinance as ef
import multitasking
import pandas as pd
import requests
from retry import retry
from tqdm import tqdm

import config
from common.decorator import cost
from common.meta import SingletonMeta
from common.utils import is_bad_stock, code_with_prefix, df_to_csv, parse_line
from stock import Stock, RealTimeQuote


# kill all tasks on ctrl-c
signal.signal(signal.SIGINT, multitasking.killall)
multitasking.set_max_threads(multitasking.cpu_count() * 2 + 1)


class MarketManager(metaclass=SingletonMeta):
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
        self.real_time_quotes_buffer = dict()
        self.max_buffer_size = 10
        self.real_time_quotes_queue = asyncio.Queue()  # 实时交易信息队列

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

    async def real_time_quotes_producer(self):
        counter = 0
        while True:
            tasks = self.fetch_real_time_quotes_coroutines_tasks()
            await asyncio.wait(tasks)
            counter += 1
            if counter >= self.max_buffer_size:
                for key in self.real_time_quotes_buffer.keys():
                    await self.real_time_quotes_queue.put(self.real_time_quotes_buffer.pop(key))
            time.sleep(1)

    async def real_time_quotes_consumer(self):
        while True:
            quotes = await self.real_time_quotes_queue.get()
            await asyncio.sleep(1)
            print("saved")

    async def fetch_all_stock_real_time_quotes(self, batch_size=200):
        progress_bar = tqdm(range(0, self.stocks_count, batch_size))
        for epoch in range(0, self.stocks_count, batch_size):
            self.fetch_real_time_quotes_by_stock_codes(self.stocks_code[epoch:epoch + batch_size], progress_bar)
        # 等待所有线程执行完毕
        multitasking.wait_for_tasks()

    @multitasking.task
    def fetch_real_time_quotes_by_stock_codes(self, stock_codes: List[str], progress_bar: tqdm):
        response = self.get_real_time_quotes(stock_codes)
        self._parse_and_update_buffer(response)
        progress_bar.update(1)
        progress_bar.set_description("fetch real time quotes")

    async def update_real_time_quotes(self, batch_size=200):
        progress_bar = tqdm(range(0, self.stocks_count, batch_size))
        for epoch in range(0, self.stocks_count, batch_size):
            self.batch_update_real_time_quotes(self.stocks_code[epoch:epoch + batch_size], progress_bar)
        # todo: 使用协程
        # 等待所有线程执行完毕
        # multitasking.wait_for_tasks()

    def batch_update_real_time_quotes(self, stock_codes: List[str], progress_bar: tqdm):
        response = self.get_real_time_quotes(stock_codes)
        self._parse_and_update(response)
        progress_bar.update(1)
        progress_bar.set_description("fetch real time data")

    def _save_to_df_and_file(self, real_time_quote: RealTimeQuote):
        new_row = pd.DataFrame([real_time_quote])
        # todo: 暂时不做数据分析，只需要把数据存下来
        # if real_time_quote.code in self.real_time_df_dict:
        #     # DataFrame的append()不改变原来的返回一个新的对象
        #     self.real_time_df_dict[real_time_quote.code] = self.real_time_df_dict[real_time_quote.code].append(new_row)
        # else:
        #     self.real_time_df_dict[real_time_quote.code] = new_row
        df_to_csv(new_row)

    def _update_real_time_quotes_buffer(self, real_time_quote: RealTimeQuote):
        if real_time_quote.code in self.real_time_quotes_buffer:
            self.real_time_quotes_buffer[real_time_quote.code].append(real_time_quote)
        else:
            self.real_time_quotes_buffer[real_time_quote.code] = [real_time_quote]

    def _parse_and_update_buffer(self, response: str):
        stock_texts = response.split("\n")
        for text in stock_texts:
            real_time_quote = parse_line(text)
            if real_time_quote:
                # self._save_to_df_and_file(real_time_quote)
                self._update_real_time_quotes_buffer(real_time_quote)

    def __load_today_quote_history(self):
        pass
