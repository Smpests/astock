import os

from chinese_calendar import is_workday

from typing import Optional, List
import pandas as pd
from tqdm import tqdm

import config
from stock import RealTimeQuote
from common.const import *


def df_to_csv(df: pd.DataFrame) -> bool:
    if not isinstance(df, pd.DataFrame):
        return False
    save_dir = os.path.join(config.RESOURCES_DIR, df.loc[0]["code"])
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    save_path = os.path.join(save_dir, f"{df.loc[0]['date']}.csv")
    try:
        df.to_csv(
            save_path,
            mode="a",
            index=False,
            encoding="utf-8",
            header=not os.path.exists(save_path)
        )
        return True
    except Exception as e:
        print(f"write to {save_path} failed")
        return False


async def quotes_to_csv(quotes: List[RealTimeQuote], drop_duplicates=True) -> bool:
    df = pd.DataFrame(quotes)
    if drop_duplicates:
        # 冷门股票可能没有数据更新，导致读到多条重复数据，在这里去重
        df.drop_duplicates(inplace=True)
    return df_to_csv(df)


def parse_line(text: str) -> Optional[RealTimeQuote]:
    text = text.strip()
    if text:
        try:
            contains_stock_code, data = text.split("=")
            stock_code = contains_stock_code[-8:]
            if not stock_code.startswith(("sz", "sh", "bj")):
                raise ValueError("invalid stock code")
            if len(data) > 3:  # 空串至少包含"";三个字符
                return RealTimeQuote(stock_code, *data[1:-1].split(",")[:32])  # 只要33位，后面的暂无意义
        except Exception as e:
            print(f"Something run while parse text:{text}")
    return None


def parse_sina_response_text(response: str) -> List[RealTimeQuote]:
    stock_texts = response.split("\n")
    quotes = []
    for text in stock_texts:
        real_time_quote = parse_line(text)
        if real_time_quote:
            quotes.append(real_time_quote)
    return quotes


def is_bad_stock(name: str) -> bool:
    for keyword in BAD_STOCK_NAME_CONTAINS:
        if keyword in name:
            return True
    return False


def code_with_prefix(code: str) -> str:
    code = code.zfill(6)
    if code.startswith(SHANGHAI_PREFIX):
        code = "sh" + code
    elif code.startswith(BEIJING_PREFIX):
        code = "bj" + code
    else:
        code = "sz" + code
    return code


def is_trade_time(_datetime: datetime) -> bool:
    """
    输入是否是交易时间
    :return: bool value
    """
    # 工作日
    if is_workday(_datetime.date()):
        if datetime.isoweekday(_datetime) < 6:  # 不是周六日(1-7表示周一至周末)
            now_time = _datetime.time()
            # 在开盘时间内
            if FIRST_OPENING_TIME < now_time < FIRST_CLOSING_TIME:
                return True
            if SECOND_OPENING_TIME < now_time < SECOND_CLOSING_TIME:
                return True
    return False


def update_progress_bar(progress_bar: tqdm):
    progress_bar.update(1)
