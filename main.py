import asyncio

from consumer import RealTimeQuotesConsumer
from producer import RealTimeQuotesProducer
from stock.market import MarketManager


async def start():
    consumer_count = 1000
    market_manager = MarketManager()
    queue = asyncio.Queue()
    producer_task = asyncio.create_task(RealTimeQuotesProducer(market_manager, queue).async_produce())
    consumer = RealTimeQuotesConsumer(market_manager, queue)
    consumer_tasks = [asyncio.create_task(consumer.async_consume()) for _ in range(consumer_count)]

    await asyncio.gather(producer_task, *consumer_tasks)


if __name__ == "__main__":
    asyncio.run(start())
