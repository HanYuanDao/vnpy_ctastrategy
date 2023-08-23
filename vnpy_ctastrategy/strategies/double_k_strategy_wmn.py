from vnpy_ctastrategy import (
    # CTA策略模版
    XinQiCtaTemplateBar,
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


class DoubleKStrategyWMN(XinQiCtaTemplateBar):

    author = "Xin Qi Technical Corporation"

    const_k2_open_low_diff = 80
    const_k2_turnover = 2800
    const_volume = 10
    const_insert_order_price_ratio = 0.333
    const_over_price_ratio = 1
    const_no_trade_tick_num = 3
    const_sleep_15k_num = 5
    super.parameters = super.parameters + [
        "const_k2_open_low_diff",
        "const_k2_turnover",
        "const_volume",
        "const_insert_order_price_ratio",
        "const_over_price_ratio",
        "const_no_trade_tick_num",
        "const_sleep_15k_num"
    ]

    xxx_k1: BarData
    xxx_k2: BarData
    xxx_insert_order_k1: BarData
    xxx_insert_order_k2: BarData
    no_trade_tick_num = 0
    sleep_15k_num = 0
    super.variables = super.variables + [
        "xxx_k1",
        "xxx_k2",
        "xxx_insert_order_k1",
        "xxx_insert_order_k2",
        "no_trade_tick_num",
        "sleep_15k_num"
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super(DoubleKStrategyWMN, self).__init__(cta_engine, strategy_name, vt_symbol, setting)

        # 调用K线生成模块 从tick数据合成分钟k线
        self.bg = BarGenerator(self.on_bar, self.const_k_level, self.on_15min_bar)

        # 调用K线时间序列管理模块
        self.am = ArrayManager(self.const_boll_window)

    def on_xq_init(self):
        # # 加载历史数据回测 加载天数
        self.load_bar(0)
        # # 加载tick数据回测 加载天数
        # self.load_tick(0)

    def on_xq_start(self):
        pass

    def on_xq_stop(self):
        pass

    def on_tick(self, tick: TickData):
        if self.is_insert_order:
            if self.no_trade_tick_num > 0:
                self.no_trade_tick_num -= 1
            else:
                self.cancel_all()

    def build_bar_parameter(self):
        if self.pos != 0:
            # 判断止损
            if (self.trade_direction == 1 and self.order_open_price < self.xxx_k2.low_price) or \
                    (self.trade_direction == 2 and self.order_open_price > self.xxx_k2.low_price):
                self.strategy_trade_memo = "order_open_price-" + str(self.order_open_price) \
                                           + "k2.low_price" + str(self.xxx_k2.low_price)
                if self.trade_direction == 1:
                    if super.is_close_mode(self.const_close_round_mode):
                        self.short(self.xxx_k2.low_price,
                                   abs(self.pos),
                                   lock=True,
                                   memo=self.strategy_trade_memo)
                    else:
                        self.sell(self.xxx_k2.low_price,
                                  abs(self.pos),
                                  net=True,
                                  memo=self.strategy_trade_memo)
                elif self.trade_direction == 2:
                    if super.is_close_mode(self.const_close_round_mode):
                        self.buy(self.xxx_k2.high_price,
                                 abs(self.pos),
                                 lock=True,
                                 memo=self.strategy_trade_memo)
                    else:
                        self.cover(self.xxx_k2.high_price,
                                   abs(self.pos),
                                   net=True,
                                   memo=self.strategy_trade_memo)
                self.write_log("止损:" + self.strategy_trade_memo)

    def on_15min_bar(self, bar: BarData):
        if not self.put_array_manager(self.am, bar):
            return

        if self.xxx_k2:
            self.xxx_k2 = bar
            return
        else:
            self.xxx_k1 = self.xxx_k2
            self.xxx_k2 = bar

        if self.pos == 0:
            # 判断开仓
            if self.sleep_15k_num > 0:
                self.sleep_15k_num -= 1
                return

            self.trade_direction = 0
            if self.xxx_k1.close_price < self.xxx_k1.open_price and \
                    self.xxx_k2.close_price > self.xxx_k2.open_price and \
                    self.xxx_k2.open_price < self.xxx_k1.close_price and \
                    self.xxx_k2.close_price > self.xxx_k1.open_price and \
                    self.xxx_k2.low_price < self.xxx_k1.low_price and \
                    self.xxx_k2.open_price - self.xxx_k2.low_price > self.const_k2_open_low_diff and \
                    self.xxx_k2.turnover > self.xxx_k1.turnover and \
                    self.xxx_k2.turnover > self.const_k2_turnover:
                self.trade_direction = 1
            elif self.xxx_k1.close_price > self.xxx_k1.open_price and \
                    self.xxx_k2.close_price < self.xxx_k2.open_price and \
                    self.xxx_k2.open_price > self.xxx_k1.close_price and \
                    self.xxx_k2.close_price < self.xxx_k1.open_price and \
                    self.xxx_k2.low_price > self.xxx_k1.low_price and \
                    self.xxx_k2.low_price - self.xxx_k2.open_price > self.const_k2_open_low_diff and \
                    self.xxx_k2.turnover > self.xxx_k1.turnover and \
                    self.xxx_k2.turnover > self.const_k2_turnover:
                self.trade_direction = 2

            if self.trade_direction != 0:
                self.no_trade_tick_num = self.const_no_trade_tick_num
                self.sleep_15k_num = self.const_sleep_15k_num
            else:
                self.xxx_insert_order_k1 = self.xxx_k1
                self.xxx_insert_order_k2 = self.xxx_k2

            if self.trade_direction == 1:
                price = self.xxx_k2.high_price \
                        - (1 / 3) * (self.xxx_k2.high_price - self.xxx_k2.low_price) \
                        + self.const_over_price_ratio * self.const_price_tick
                volume = self.const_volume
                if super.is_close_mode(self.const_close_round_mode):
                    self.xq_buy(price,
                                volume,
                                lock=True,
                                memo=self.strategy_trade_memo)
                else:
                    self.xq_buy(price,
                                volume,
                                net=True,
                                memo=self.strategy_trade_memo)
            elif self.trade_direction == 2:
                price = self.xxx_k2.low_price \
                        + (1 / 3) * (self.xxx_k2.high_price - self.xxx_k2.low_price) \
                        - self.const_over_price_ratio * self.const_price_tick
                volume = self.const_volume
                if super.is_close_mode(self.const_close_round_mode):
                    self.xq_short(price,
                                  volume,
                                  lock=True,
                                  memo=self.strategy_trade_memo)
                else:
                    self.xq_short(price,
                                  volume,
                                  net=True,
                                  memo=self.strategy_trade_memo)
        else:
            # 判断止盈
            if (self.trade_direction == 1 and self.xxx_k2.turnover > self.xxx_insert_order_k1.turnover) or \
                (self.trade_direction == 2 and self.xxx_k2.turnover < self.xxx_insert_order_k1.turnover):
                self.strategy_trade_memo = "trade_direction-" + str(self.trade_direction) \
                                           + "k2.turnover" + str(self.xxx_k2.turnover) \
                                           + "insert_order_k1.turnover" + str(self.xxx_insert_order_k1.turnover)
                if self.trade_direction == 1:
                    if super.is_close_mode(self.const_close_round_mode):
                        self.short(self.xxx_k2.low_price,
                                   abs(self.pos),
                                   lock=True,
                                   memo=self.strategy_trade_memo)
                    else:
                        self.sell(self.xxx_k2.low_price,
                                  abs(self.pos),
                                  net=True,
                                  memo=self.strategy_trade_memo)
                elif self.trade_direction == 2:
                    if super.is_close_mode(self.const_close_round_mode):
                        self.buy(self.xxx_k2.high_price,
                                 abs(self.pos),
                                 lock=True,
                                 memo=self.strategy_trade_memo)
                    else:
                        self.cover(self.xxx_k2.high_price,
                                   abs(self.pos),
                                   net=True,
                                   memo=self.strategy_trade_memo)
                self.write_log("止盈:" + self.strategy_trade_memo)

    def build_order_parameter(self, order: OrderData):
        pass

    def build_trade_parameter(self, trade: TradeData):
        pass


