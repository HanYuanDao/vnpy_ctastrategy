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


class TheBollTacticOfND(CtaTemplate):
    # 声明作者
    author = "Xin Qi Technical Corporation"

    const_flag_close_mode = 'lock'

    const_boll_window = 20
    const_boll_dev = 2
    const_volume = 1
    const_num_trend = 15
    const_boll_mid_price_range = 1.005
    const_loss_thr = 0.015
    const_profit_thr = 0.04
    const_close_round_mode = "lock"
    parameters = [
        "const_volume",
        "const_num_trend",
        "const_boll_mid_price_range",
        "const_loss_thr",
        "const_profit_thr",
        "const_close_round_mode",
    ]

    tick_now: TickData = None
    # 当前回合开仓的价格
    open_price = 0.0
    num_trend = 0
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
    variables = [
        "tick_now",
        "num_trend",
        "trade_direction",
        "strategy_trade_state",
        "strategy_trade_memo"
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super(TheBollTacticOfND, self).__init__(cta_engine, strategy_name, vt_symbol, setting)

        # 调用K线生成模块 从tick数据合成分钟k线
        self.bg = BarGenerator(self.on_bar, 15, self.on_15min_bar)

        # 调用K线时间序列管理模块
        self.am = ArrayManager(self.const_boll_window)

    def on_init(self):
        self.write_log("策略初始化")

        # # 加载历史数据回测 加载10天
        self.load_bar(0)
        # # 加载tick数据回测 加载30天
        self.load_tick(0)

        self.reset_tmp_variable()

    def on_start(self):
        self.write_log("策略启动")

    def on_stop(self):
        self.write_log("策略停止")

    def on_15min_bar(self, bar: BarData):
        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return

        self.boll_up, self.boll_down = am.boll(self.const_boll_window, self.const_boll_dev)

        self.boll_mid = (self.boll_up + self.boll_down) / 2
        if bar.high_price < self.boll_mid:
            self.num_trend -= 1
        elif bar.low_price > self.boll_mid:
            self.num_trend += 1
        else:
            self.num_trend = 0

        if self.pos == 0 and abs(self.num_trend) >= self.const_num_trend \
                and abs(self.tick_now.last_price - self.boll_mid) < self.boll_mid * self.const_boll_mid_price_range:
            if self.num_trend > 0:
                self.trade_direction = 1
                if self.const_flag_close_mode.__eq__(self.const_close_round_mode):
                    self.buy(self.get_highest_price(self.tick_now),
                             self.const_volume,
                             lock=True,
                             memo=self.strategy_trade_memo)
                else:
                    self.buy(self.get_highest_price(self.tick_now),
                             self.const_volume,
                             net=True,
                             memo=self.strategy_trade_memo)
            else:
                self.trade_direction = 2
                if self.const_flag_close_mode.__eq__(self.const_close_round_mode):
                    self.short(self.get_lowest_price(self.tick_now),
                               self.const_volume,
                               lock=True,
                               memo=self.strategy_trade_memo)
                else:
                    self.short(self.get_lowest_price(self.tick_now),
                               self.const_volume,
                               net=True,
                               memo=self.strategy_trade_memo)

    def on_tick(self, tick: TickData):
        self.tick_now = tick
        self.bg.update_tick(tick)

        # if self.tick_now.datetime.month == 2 \
        #     and self.tick_now.datetime.day == 1 \
        #     and self.tick_now.datetime.hour == 13 \
        #     and self.tick_now.datetime.minute == 30:

        if self.pos != 0:
            diff = self.tick_now.last_price - self.open_price

            if (self.trade_direction == 1 and diff < 0) \
                    or (self.trade_direction == 2 and diff > 0):
                # 止损判断
                if abs(diff) > self.open_price * self.const_loss_thr:
                    if self.trade_direction == 1:
                        if self.const_flag_close_mode.__eq__(self.const_close_round_mode):
                            self.short(self.get_lowest_price(self.tick_now),
                                       abs(self.pos),
                                       lock=True,
                                       memo=self.strategy_trade_memo)
                        else:
                            self.sell(self.get_lowest_price(self.tick_now),
                                      abs(self.pos),
                                      net=True,
                                      memo=self.strategy_trade_memo)
                    else:
                        if self.const_flag_close_mode.__eq__(self.const_close_round_mode):
                            self.buy(self.get_highest_price(self.tick_now),
                                     abs(self.pos),
                                     lock=True,
                                     memo=self.strategy_trade_memo)
                        else:
                            self.cover(self.get_highest_price(self.tick_now),
                                       abs(self.pos),
                                       net=True,
                                       memo=self.strategy_trade_memo)
            else:
                # 止盈判断
                if abs(diff) > self.open_price * self.const_profit_thr:
                    if self.trade_direction == 1:
                        if self.const_flag_close_mode.__eq__(self.const_close_round_mode):
                            self.short(self.get_lowest_price(self.tick_now),
                                       abs(self.pos),
                                       lock=True,
                                       memo=self.strategy_trade_memo)
                        else:
                            self.sell(self.get_lowest_price(self.tick_now),
                                      abs(self.pos),
                                      net=True,
                                      memo=self.strategy_trade_memo)
                    else:
                        if self.const_flag_close_mode.__eq__(self.const_close_round_mode):
                            self.buy(self.get_highest_price(self.tick_now),
                                     abs(self.pos),
                                     lock=True,
                                     memo=self.strategy_trade_memo)
                        else:
                            self.cover(self.get_highest_price(self.tick_now),
                                       abs(self.pos),
                                       net=True,
                                       memo=self.strategy_trade_memo)

    def on_bar(self, bar: BarData):
        self.bg.update_bar(bar)

    def on_order(self, order: OrderData):
        pass

    def on_trade(self, trade: TradeData):
        self.open_price = trade.price
        pass

    def reset_tmp_variable(self):
        self.tick_now: TickData = None
        self.open_price = 0.0
        self.num_trend = 0
        self.trade_direction = 0
        self.strategy_trade_state = 0
        self.strategy_trade_memo = ""

    def get_highest_price(self, tick: TickData):
        return tick.limit_down
    def get_lowest_price(self, tick: TickData):
        return tick.limit_up