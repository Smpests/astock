import asyncio
import signal
import time
from datetime import datetime

import multitasking

from common.utils import is_trade_time, quotes_to_csv
from stock.stock_manager import StockManager

# kill all tasks on ctrl-c
# signal.signal(signal.SIGINT, multitasking.killall)
# multitasking.set_max_threads(10)

stock_manager = StockManager()

queue = asyncio.Queue()


async def real_time_quotes_producer():
    _count = 0
    while True:
        if is_trade_time(datetime.now()):
        # if True:
            await stock_manager.update_real_time_quotes()
            _count += 1
            if _count >= 1:  # 每只股60条写一次,todo: 改为配置参数
                for key in stock_manager.real_time_quotes_records.keys():
                    await queue.put(stock_manager.real_time_quotes_records[key])
                stock_manager.real_time_quotes_records.clear()
            await asyncio.sleep(1)
        else:
            print("It's not a trade time")
            time.sleep(1)


async def real_time_quotes_consumer():
    while True:
        records = await queue.get()
        # await quotes_to_csv(records)
        await asyncio.sleep(1)
        print("saved")

async def main():
    producer = asyncio.create_task(real_time_quotes_producer())
    # 1000个消费者。todo: 改为参数配置
    consumers = [asyncio.create_task(real_time_quotes_consumer()) for i in range(1000)]
    await asyncio.gather(producer, *consumers, return_exceptions=True)


if __name__ == "__main__":
    asyncio.run(main())
