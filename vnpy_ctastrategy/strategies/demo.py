from vnpy_ctastrategy import (
    # CTA策略模版
    # 以下五个均为储存对应信息的数据容器
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    # K线生成模块
    BarGenerator,
    # K线时间序列管理模块
    ArrayManager
)

from abc import ABC


class Demo4Debug(ABC):
