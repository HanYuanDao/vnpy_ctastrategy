from vnpy_ctastrategy import (
    # CTA策略模版
    CtaTemplate,
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
from vnpy.trader.constant import Status
from datetime import datetime
from collections import deque


class DoubleKStrategyWMN(CtaTemplate):
    author = "Xin Qi Technical Corporation"

    parameters = [

    ]

    is_insert_order = False
    variables = [
        "is_insert_order",
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super(DoubleKStrategyWMN, self).__init__(cta_engine, strategy_name, vt_symbol, setting)

        # 调用K线生成模块 从tick数据合成分钟k线
        self.bg = BarGenerator(self.on_bar, self.const_k_level, self.on_15min_bar)

        # 调用K线时间序列管理模块
        self.am = ArrayManager(self.const_boll_window)

        self.tick_now: TickData = None
        self.bar_now: BarData = None

    def on_init(self):
        self.write_log("策略初始化")

        self.reset_tmp_variable()

        # # 加载历史数据回测 加载天数
        self.load_bar(0)
        # # 加载tick数据回测 加载天数
        # self.load_tick(0)

    def on_start(self):
        self.is_insert_order = False
        self.write_log("策略启动")

    def on_stop(self):
        self.write_log("策略停止")

    def on_bar(self, bar: BarData):
        self.bg.update_bar(bar)

        self.bar_now = bar

    def on_15min_bar(self, bar: BarData):
        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return

    def on_tick(self, tick: TickData):
        pass

    def on_order(self, order: OrderData):
        if order.status == Status.CANCELLED \
                or order.status == Status.REJECTED:
            self.is_insert_order = False

    def on_trade(self, trade: TradeData):
        if self.is_insert_order:
            self.is_insert_order = False

        pass

