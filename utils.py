import os
from common.const import BAD_STOCK_NAME_CONTAINS, SHANGHAI_PREFIX, BEIJING_PREFIX
from typing import Optional
import pandas as pd

import config
from stock import RealTimeQuote


def df_to_csv(df: pd.DataFrame):
    save_dir = os.path.join(config.RESOURCES_DIR, df.loc[0]["code"])
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    save_path = os.path.join(save_dir, f"{df.loc[0]['date']}.csv")
    df.to_csv(
        save_path,
        mode="a",
        index=False,
        encoding="utf-8",
        header=not os.path.exists(save_path)
    )


def parse_sina_response_text(text: str) -> Optional[RealTimeQuote]:
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
