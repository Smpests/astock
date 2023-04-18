import asyncio
import time
from datetime import datetime

from common.utils import is_trade_time
from producer._base import BaseProducer
from stock.market import MarketManager


class RealTimeQuotesProducer(BaseProducer):

    def __init__(self, market_manager: MarketManager, queue: asyncio.Queue):
        super().__init__()
        self.market_manager = market_manager
        self.queue = queue

    def produce(self):
        pass

    async def async_produce(self):
        counter = 0
        while True:
            if is_trade_time(datetime.now()):
                await self.market_manager.fetch_all_stock_real_time_quotes()
                counter += 1
                if counter >= self.market_manager.max_buffer_size:
                    for key in list(self.market_manager.real_time_quotes_buffer.keys()):
                        await self.queue.put(self.market_manager.real_time_quotes_buffer.pop(key))
                    counter = 0
                await asyncio.sleep(1)
            else:
                print("It's not a trade time now.")
                time.sleep(1)


