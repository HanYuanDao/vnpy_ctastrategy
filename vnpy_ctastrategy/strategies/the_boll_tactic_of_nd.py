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


class TheBollTacticOfND(CtaTemplate):
    # 声明作者
    author = "Xin Qi Technical Corporation"

    const_flag_close_mode = 'lock'

    const_boll_window = 20
    const_boll_dev = 2

    const_jeton = 1000000
    const_k_level = 15
    const_num_trend = 14
    const_boll_mid_price_range = 0.005
    const_loss_thr = 0.015
    const_profit_thr = 0.04
    const_close_round_mode = "lock"
    const_deque_size = 1200
    const_diff_ratio = 1.02
    const_highest_price_queue: deque
    const_lowest_price_queue: deque
    parameters = [
        "const_boll_window",
        "const_boll_dev",
        "const_jeton",
        "const_k_level",
        "const_num_trend",
        "const_boll_mid_price_range",
        "const_diff_ratio",
        "const_loss_thr",
        "const_profit_thr",
        "const_close_round_mode",
        "const_deque_size",
    ]

    # 当前回合开仓的价格
    open_price = 0.0
    xxx_num_trend = 0
    # 交易方向
    # 0为初始状态 1为多 2为空
    trade_direction = 0
    # 策略交易的状态
    # 0：不进行任何活动
    # 1：开始开仓
    # 5：已持仓
    # 10：开始止损
    # 20：开始止盈（超5平仓）
    # 21：开始止盈（超2平仓）
    # 91: 转为休眠
    # 92: 首次清理持仓
    # 93: 确认持仓清理完毕
    strategy_trade_state = 0
    strategy_trade_memo = ''
    is_insert_order = False
    xxx_boll_mid_price_range = 0
    xxx_diff_ratio = 0
    xxx_loss_thr = 0
    xxx_profit_thr = 0
    variables = [
        "open_price",
        "xxx_num_trend",
        "xxx_boll_mid_price_range",
        "xxx_diff_ratio",
        "xxx_loss_thr",
        "xxx_profit_thr",
        "trade_direction",
        "strategy_trade_state",
        "strategy_trade_memo",
        "is_insert_order"
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super(TheBollTacticOfND, self).__init__(cta_engine, strategy_name, vt_symbol, setting)

        # 调用K线生成模块 从tick数据合成分钟k线
        self.bg = BarGenerator(self.on_bar, self.const_k_level, self.on_15min_bar)

        # 调用K线时间序列管理模块
        self.am = ArrayManager(self.const_boll_window)

        self.const_highest_price_queue = deque(maxlen=self.const_deque_size)
        self.const_lowest_price_queue = deque(maxlen=self.const_deque_size)

        self.tick_now: TickData = None
        self.bar_now: BarData = None

    def on_init(self):
        self.write_log("策略初始化")

        self.reset_tmp_variable()

        # # 加载历史数据回测 加载10天
        self.load_bar(8)
        # # 加载tick数据回测 加载30天
        # self.load_tick(0)

    def on_start(self):
        self.is_insert_order = False
        self.write_log("策略启动")

    def on_stop(self):
        self.write_log("策略停止")

    def on_bar(self, bar: BarData):
        self.bg.update_bar(bar)

        self.bar_now = bar

        self.const_highest_price_queue.append(bar.high_price)
        self.const_lowest_price_queue.append(bar.low_price)

        # if len(self.const_highest_price_queue) < self.const_deque_size or \
        #         len(self.const_lowest_price_queue) < self.const_deque_size:
        #     return
        #
        # if self.pos != 0:
        #     diff = self.bar_now.close_price - self.open_price
        #
        #     if (self.trade_direction == 1 and diff < 0) \
        #             or (self.trade_direction == 2 and diff > 0):
        #         # 止损判断
        #         if abs(diff) > self.open_price * self.const_loss_thr:
        #             if self.trade_direction == 1:
        #                 if self.const_flag_close_mode.__eq__(self.const_close_round_mode):
        #                     self.short(self.get_lowest_price_bar(self.bar_now),
        #                                abs(self.pos),
        #                                lock=True,
        #                                memo=self.strategy_trade_memo)
        #                 else:
        #                     self.sell(self.get_lowest_price_bar(self.bar_now),
        #                               abs(self.pos),
        #                               net=True,
        #                               memo=self.strategy_trade_memo)
        #             else:
        #                 if self.const_flag_close_mode.__eq__(self.const_close_round_mode):
        #                     self.buy(self.get_highest_price_bar(self.bar_now),
        #                              abs(self.pos),
        #                              lock=True,
        #                              memo=self.strategy_trade_memo)
        #                 else:
        #                     self.cover(self.get_highest_price_bar(self.bar_now),
        #                                abs(self.pos),
        #                                net=True,
        #                                memo=self.strategy_trade_memo)
        #     else:
        #         # 止盈判断
        #         if abs(diff) > self.open_price * self.const_profit_thr:
        #             if self.trade_direction == 1:
        #                 if self.const_flag_close_mode.__eq__(self.const_close_round_mode):
        #                     self.short(self.get_lowest_price_bar(self.bar_now),
        #                                abs(self.pos),
        #                                lock=True,
        #                                memo=self.strategy_trade_memo)
        #                 else:
        #                     self.sell(self.get_lowest_price_bar(self.bar_now),
        #                               abs(self.pos),
        #                               net=True,
        #                               memo=self.strategy_trade_memo)
        #             else:
        #                 if self.const_flag_close_mode.__eq__(self.const_close_round_mode):
        #                     self.buy(self.get_highest_price_bar(self.bar_now),
        #                              abs(self.pos),
        #                              lock=True,
        #                              memo=self.strategy_trade_memo)
        #                 else:
        #                     self.cover(self.get_highest_price_bar(self.bar_now),
        #                                abs(self.pos),
        #                                net=True,
        #                                memo=self.strategy_trade_memo)
        # else:
        #     if self.tick_now.datetime.day > 15:
        #         return
        #     if abs(self.xxx_num_trend) >= self.const_num_trend and \
        #             abs(self.bar_now.close_price - self.boll_mid) < self.boll_mid * self.const_boll_mid_price_range and \
        #             max(self.const_highest_price_queue) >= min(self.const_lowest_price_queue) * self.const_diff_ratio:
        #         volume = int(self.const_jeton / self.get_symbol_margin()
        #                      / self.bar_now.close_price / self.get_symbol_size())
        #         if self.xxx_num_trend > 0:
        #             self.trade_direction = 1
        #             if self.const_flag_close_mode.__eq__(self.const_close_round_mode):
        #                 self.buy(self.get_highest_price_bar(self.bar_now),
        #                          volume,
        #                          lock=True,
        #                          memo=self.strategy_trade_memo)
        #             else:
        #                 self.buy(self.get_highest_price_bar(self.bar_now),
        #                          volume,
        #                          net=True,
        #                          memo=self.strategy_trade_memo)
        #         else:
        #             self.trade_direction = 2
        #             if self.const_flag_close_mode.__eq__(self.const_close_round_mode):
        #                 self.short(self.get_lowest_price_bar(self.bar_now),
        #                            volume,
        #                            lock=True,
        #                            memo=self.strategy_trade_memo)
        #             else:
        #                 self.short(self.get_lowest_price_bar(self.bar_now),
        #                            volume,
        #                            net=True,
        #                            memo=self.strategy_trade_memo)

    def on_15min_bar(self, bar: BarData):
        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return

        self.boll_up, self.boll_down = am.boll(self.const_boll_window, self.const_boll_dev)

        self.boll_mid = (self.boll_up + self.boll_down) / 2
        if bar.high_price < self.boll_mid:
            if self.xxx_num_trend <= 0:
                self.xxx_num_trend -= 1
            else:
                self.xxx_num_trend = -1
        elif bar.low_price > self.boll_mid:
            if self.xxx_num_trend >= 0:
                self.xxx_num_trend += 1
            else:
                self.xxx_num_trend = 1
        else:
            self.xxx_num_trend = 0

    def on_tick(self, tick: TickData):
        self.tick_now = tick
        # 将tick数据推送给bg以使其生成k线
        self.bg.update_tick(tick)

        if len(self.const_highest_price_queue) < self.const_deque_size or \
                len(self.const_lowest_price_queue) < self.const_deque_size:
            return

        if self.pos != 0:
            diff = self.tick_now.last_price - self.open_price

            if (self.trade_direction == 1 and diff < 0) \
                    or (self.trade_direction == 2 and diff > 0):
                # 止损判断
                self.xxx_loss_thr = abs(diff) / self.open_price
                if self.xxx_loss_thr > self.const_loss_thr:
                    if self.is_insert_order.__eq__(False):
                        self.is_insert_order = True

                        self.strategy_trade_memo = "self.xxx_loss_thr-" + str(self.xxx_loss_thr)
                        if self.trade_direction == 1:
                            if self.const_flag_close_mode.__eq__(self.const_close_round_mode):
                                self.short(self.get_lowest_price_tick(self.tick_now),
                                           abs(self.pos),
                                           lock=True,
                                           memo=self.strategy_trade_memo)
                            else:
                                self.sell(self.get_lowest_price_tick(self.tick_now),
                                          abs(self.pos),
                                          net=True,
                                          memo=self.strategy_trade_memo)
                        else:
                            if self.const_flag_close_mode.__eq__(self.const_close_round_mode):
                                self.buy(self.get_highest_price_tick(self.tick_now),
                                         abs(self.pos),
                                         lock=True,
                                         memo=self.strategy_trade_memo)
                            else:
                                self.cover(self.get_highest_price_tick(self.tick_now),
                                           abs(self.pos),
                                           net=True,
                                           memo=self.strategy_trade_memo)
                        self.write_log("止损:" + self.strategy_trade_memo)
            else:
                # 止盈判断
                self.xxx_profit_thr = abs(diff) / self.open_price
                if self.xxx_profit_thr > self.const_profit_thr:
                    if self.is_insert_order.__eq__(False):
                        self.is_insert_order = True

                        self.strategy_trade_memo = "self.xxx_profit_thr-" + str(self.xxx_profit_thr)
                        if self.trade_direction == 1:
                            if self.const_flag_close_mode.__eq__(self.const_close_round_mode):
                                self.short(self.get_lowest_price_tick(self.tick_now),
                                           abs(self.pos),
                                           lock=True,
                                           memo=self.strategy_trade_memo)
                            else:
                                self.sell(self.get_lowest_price_tick(self.tick_now),
                                          abs(self.pos),
                                          net=True,
                                          memo=self.strategy_trade_memo)
                        else:
                            if self.const_flag_close_mode.__eq__(self.const_close_round_mode):
                                self.buy(self.get_highest_price_tick(self.tick_now),
                                         abs(self.pos),
                                         lock=True,
                                         memo=self.strategy_trade_memo)
                            else:
                                self.cover(self.get_highest_price_tick(self.tick_now),
                                           abs(self.pos),
                                           net=True,
                                           memo=self.strategy_trade_memo)
                        self.write_log("止盈:" + self.strategy_trade_memo)
        else:
            # if self.tick_now.datetime.day > 15:
            #     return

            if (abs(self.xxx_num_trend) >= self.const_num_trend).__eq__(False):
                return

            self.xxx_boll_mid_price_range = abs(self.tick_now.last_price - self.boll_mid) / self.boll_mid
            if (self.xxx_boll_mid_price_range < self.const_boll_mid_price_range).__eq__(False):
                return

            self.xxx_diff_ratio = max(self.const_highest_price_queue) / min(self.const_lowest_price_queue)
            if (self.xxx_diff_ratio >= self.const_diff_ratio).__eq__(False):
                return

            if self.is_insert_order.__eq__(False):
                self.is_insert_order = True
                volume = int(self.const_jeton / self.get_symbol_margin() / self.tick_now.last_price / self.get_symbol_size())

                self.strategy_trade_memo = "self.xxx_num_trend-" + str(self.xxx_num_trend) \
                                           + " self.xxx_boll_mid_price_range-" + str(self.xxx_boll_mid_price_range) \
                                           + " self.xxx_diff_ratio-" + str(self.xxx_diff_ratio)
                if self.xxx_num_trend > 0:
                    self.trade_direction = 1
                    if self.const_flag_close_mode.__eq__(self.const_close_round_mode):
                        self.buy(self.get_highest_price_tick(self.tick_now),
                                 volume,
                                 lock=True,
                                 memo=self.strategy_trade_memo)
                    else:
                        self.buy(self.get_highest_price_tick(self.tick_now),
                                 volume,
                                 net=True,
                                 memo=self.strategy_trade_memo)
                else:
                    self.trade_direction = 2
                    if self.const_flag_close_mode.__eq__(self.const_close_round_mode):
                        self.short(self.get_lowest_price_tick(self.tick_now),
                                   volume,
                                   lock=True,
                                   memo=self.strategy_trade_memo)
                    else:
                        self.short(self.get_lowest_price_tick(self.tick_now),
                                   volume,
                                   net=True,
                                   memo=self.strategy_trade_memo)

                if self.trading:
                    self.write_log("报单:" + self.strategy_trade_memo)

    def on_order(self, order: OrderData):
        if order.status.__eq__(Status.CANCELLED) \
                or order.status.__eq__(Status.REJECTED):
            self.is_insert_order = False

    def on_trade(self, trade: TradeData):
        self.is_insert_order = False

        self.open_price = trade.price
        pass

    def reset_tmp_variable(self):
        self.tick_now: TickData = None
        self.bar_now: BarData = None
        self.open_price = 0.0
        self.xxx_num_trend = 0
        self.trade_direction = 0
        self.strategy_trade_state = 0
        self.strategy_trade_memo = ""

        self.const_highest_price_queue = deque(maxlen=self.const_deque_size)
        self.const_lowest_price_queue = deque(maxlen=self.const_deque_size)

        self.is_insert_order = False

        self.xxx_boll_mid_price_range = 0
        self.xxx_diff_ratio = 0
        self.xxx_loss_thr = 0
        self.xxx_profit_thr = 0

    def get_highest_price_tick(self, tick: TickData):
        return tick.limit_up

    def get_lowest_price_tick(self, tick: TickData):
        return tick.limit_down

    def get_highest_price_bar(self, bar: BarData):
        return bar.upper_limit_price

    def get_lowest_price_bar(self, bar: BarData):
        return bar.lower_limit_price
