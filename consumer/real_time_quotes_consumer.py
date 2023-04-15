import asyncio
import consumer._base
from common.utils import quotes_to_csv
from stock.market import MarketManager


class RealTimeQuotesConsumer(consumer._base.BaseConsumer):

    def __init__(self, market_manager: MarketManager, queue: asyncio.Queue):
        super().__init__()
        self.market_manager = market_manager
        self.queue = queue

    def consume(self, *args, **kwargs):
        pass

    async def async_consume(self):
        while True:
            quotes = await self.queue.get()
            await quotes_to_csv(quotes)
