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

from vnpy.trader.constant import Interval

import numpy as np
from queue import Queue

import datetime as dt
import pytz
import queue
import collections
import time

"""
展示基础策略
"""


class OwnGoal(CtaTemplate):
    # 声明作者
    author = "Jason Han"

    # 声明参数，由交易员指定
    const_volume = 1
    const_ratio_long_short_stopprofit = 3
    const_ratio_long_short_open = 0.5
    const_overprice = 10
    const_last_price_offset_sec = 5
    const_ratio_max_min_last_price = 1.005
    const_max_tick_num_profit = 50
    const_max_tick_num_loss = 20
    const_max_backtest_ratio = 0.7
    const_profit_max_drawdown_ratio = 0.7
    const_max_min_last_price_offset_sec = 5 * 60
    parameters = [
        "const_volume",
        "const_ratio_long_short_stopprofit",
        "const_ratio_long_short_open",
        "const_overprice",
        "const_last_price_offset_sec",
        "const_ratio_max_min_last_price",
        "const_max_tick_num_profit",
        "const_max_tick_num_loss",
        "const_max_backtest_ratio",
        "const_profit_max_drawdown_ratio",
        "const_max_min_last_price_offset_sec",
    ]

    # 声明变量，在程序运行时变化
    price_tick = 0
    """ 
         行情历史变量
    """
    mean_price_tick_queue: collections.deque = collections.deque()
    mean_price_tick_queue_size = 0
    mean_price_5s = 0
    trade_price_tick_queue: collections.deque = collections.deque()
    trade_price_tick_queue_size = 0
    max_min_last_price_queue: collections.deque = collections.deque()
    max_min_last_price_queue_size = 0
    max_last_price_5min = 0.0
    min_last_price_5min = 0.0
    # 策略是否启动
    strategy_running = False
    # 策略交易的状态，0：不进行任何活动；1：开始开仓；5：已持仓；10：开始止损；20：开始止盈
    strategy_trade_state = 0
    strategy_trade_memo = ""
    """ 持仓中变量 """
    # 开仓价格
    open_price = 0.0
    tick_num_profit = 0
    tick_num_loss = 0
    # 期货账号盈利最大值
    profit_max_value = 0.0
    # 期货账号盈利当前值
    profit_now_value = 0.0
    max_price_tick: TickData
    insert_order_num = 0
    variables = [
        "price_tick",
        "strategy_running",
        "strategy_trade_state",
        "strategy_trade_memo",
        "tickdata_list",
        "open_price",
        "tick_num_profit",
        "tick_num_loss",
        "profit_max_value",
        "profit_now_value",
        "mean_price_tick_queue",
        "trade_price_tick_queue",
        "mean_price_5s",
        "mean_price_tick_queue_size",
        "trade_price_tick_queue_size",
        "max_price_tick",
        "insert_order_num",
        "max_min_last_price_queue",
        "max_min_last_price_queue_size",
        "max_last_price_5min",
        "min_last_price_5min"
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        # 调用K线生成模块，从tick数据合成分钟k线
        self.bg = BarGenerator(self.on_bar, 1, self.on_4tick_bar, Interval.TICK)

        # 调用K线时间序列管理模块
        self.am = ArrayManager()

    """
    CatTemplate中以on开头的函数都是回调函数，用来接受数据和状态变更。
    """

    # 策略初始化
    def on_init(self):
        self.write_log("策略初始化")

        # 加载历史数据回测，加载10天
        self.load_bar(1)
        # 加载tick数据回测，加载30天
        self.load_tick(1)

        self.price_tick = 0
        self.mean_price_tick_queue: collections.deque = collections.deque()
        self.mean_price_tick_queue_size = 0
        self.mean_price_5s = 0
        self.trade_price_tick_queue: collections.deque = collections.deque()
        self.trade_price_tick_queue_size = 0
        self.max_min_last_price_queue: collections.deque = collections.deque()
        self.max_min_last_price_queue_size = 0
        self.max_last_price_5min = 0.0
        self.min_last_price_5min = 0.0
        self.strategy_running = False
        self.strategy_trade_state = 0
        self.strategy_trade_memo = ""
        self.open_price = 0.0
        self.tick_num_profit = 0
        self.tick_num_loss = 0
        self.profit_max_value = 0.0
        self.profit_now_value = 0.0
        self.max_price_tick = TickData
        self.insert_order_num = 0

    # 策略启动
    def on_start(self):
        self.write_log("策略启动")

        # 通知图形界面更新（策略最新状态）
        # 不调用该函数则界面不会变化
        self.put_event()

    # 策略停止
    def on_stop(self):
        self.write_log("策略停止")

        # 通知图形界面更新（策略最新状态）
        # 不调用该函数则界面不会变化
        self.put_event()

    # 获得tick数据推送
    def on_tick(self, tick: TickData):
        # 将tick数据推送给bg以使其生成k线
        self.bg.update_tick(tick)

        # 去除非交易时间的数据
        if tick.datetime.hour <= 8 or 12 < tick.datetime.hour < 21:
            return

        # 基于tick级高频交易的特点，如果跨天则重置之前的临时变量
        if self.mean_price_tick_queue_size != 0:
            t = self.mean_price_tick_queue.popleft()
            if t.datetime.day != tick.datetime.day:
                self.mean_price_tick_queue.clear()
                self.mean_price_tick_queue_size = 0
                self.trade_price_tick_queue.clear()
                self.trade_price_tick_queue_size = 0
                self.strategy_running = False
            # 策略进行的成交均价队列数量足够
            else:
                self.mean_price_tick_queue.appendleft(t)

        # 交易逻辑判断
        if self.mean_price_tick_queue_size != 0:
            if self.strategy_trade_state == 1 and self.pos >= 0:
                self.insert_order4open(tick)
            elif self.strategy_trade_state == 10 and self.pos < 0:
                self.insert_order4stop_loss(tick)
            elif self.strategy_trade_state == 20 and self.pos < 0:
                self.close4stop_profit(tick)
            else:
                t = self.mean_price_tick_queue.popleft()
                tick_datetime = int(time.mktime(tick.datetime.timetuple())) * 1000 + int(
                    tick.datetime.microsecond / 1000)
                t_datetime = int(time.mktime(t.datetime.timetuple())) * 1000 + int(t.datetime.microsecond / 1000)
                if (tick_datetime - t_datetime) >= self.const_last_price_offset_sec:
                    self.trade_strategy(tick)
                self.mean_price_tick_queue.appendleft(t)

        self.build_quot_parameter(tick)

        if self.pos == 0 and self.strategy_running and self.strategy_trade_state != 1:
            if (0.0 < self.profit_now_value < self.profit_max_value * self.const_profit_max_drawdown_ratio) \
              or (self.profit_now_value < -10000):
                self.build_last_price_5min()
                if self.max_last_price_5min <= self.min_last_price_5min * self.const_ratio_max_min_last_price:
                    self.strategy_running = False

    # 获得bar数据推送
    def on_bar(self, bar: BarData):
        # 需要bg生成更周期的k线时，将分钟k线再推送给bg
        self.bg.update_bar(bar)
        # self.am.update_bar(bar)

    def on_4tick_bar(self, bar: BarData):
        """"""
        self.put_event()

    """
    委托状态更新
    """

    # 策略委托回报
    def on_order(self, order: OrderData):
        # 通知图形界面更新（策略最新状态）
        # 不调用该函数则界面不会变化
        self.put_event()

    # 策略成交回报
    def on_trade(self, trade: TradeData):
        # 通知图形界面更新（策略最新状态）
        # 不调用该函数则界面不会变化

        self.build_trade_parameter(trade)

        self.put_event()

    # 策略停止单回报
    def on_stop_order(self, stop_order: StopOrder):
        # 通知图形界面更新（策略最新状态）
        # 不调用该函数则界面不会变化
        self.put_event()

    # 编辑行情相关变量
    def build_quot_parameter(self, tick: TickData):
        tick_datetime = int(time.mktime(tick.datetime.timetuple())) * 1000 + int(tick.datetime.microsecond / 1000)

        # 添加最新的tick数据到最近五秒平均价格列表
        self.mean_price_5s = \
            (self.mean_price_5s * self.mean_price_tick_queue_size + tick.last_price) / \
            (self.mean_price_tick_queue_size + 1)
        self.mean_price_tick_queue.append(tick)
        self.mean_price_tick_queue_size += 1

        # 最近五秒平均价格列表中剔除不需要的元素
        while self.mean_price_tick_queue_size > 1:
            mpt = self.mean_price_tick_queue.popleft()
            self.mean_price_tick_queue_size -= 1
            mpt_datetime = int(time.mktime(mpt.datetime.timetuple())) * 1000 + int(mpt.datetime.microsecond / 1000)
            if tick_datetime - mpt_datetime <= self.const_last_price_offset_sec * 1000:
                self.mean_price_tick_queue.appendleft(mpt)
                self.mean_price_tick_queue_size += 1
                break
            else:
                self.mean_price_5s = \
                    (self.mean_price_5s * (self.mean_price_tick_queue_size + 1) - mpt.last_price) / \
                    self.mean_price_tick_queue_size
                continue

        # 添加最新的tick数据到最近三秒交易价格列表
        self.trade_price_tick_queue.append(tick)
        self.trade_price_tick_queue_size += 1

        # 最近三秒交易价格列表中剔除不需要的元素
        while self.trade_price_tick_queue_size > 1:
            tpt = self.trade_price_tick_queue.popleft()
            self.trade_price_tick_queue_size -= 1
            tpt_datetime = int(time.mktime(tpt.datetime.timetuple())) * 1000 + int(tpt.datetime.microsecond / 1000)
            if tick_datetime - tpt_datetime <= 3000:
                self.trade_price_tick_queue.appendleft(tpt)
                self.trade_price_tick_queue_size += 1
                break

        # 添加最新的tick数据到最近五分钟交易数据列表
        self.max_min_last_price_queue.append(tick)
        self.max_min_last_price_queue_size += 1

        # 最近五分钟交易价格列表中提出不需要的元素
        while self.max_min_last_price_queue_size > 1:
            mmpt = self.max_min_last_price_queue.popleft()
            self.max_min_last_price_queue_size -= 1
            mmpt_datetime = int(time.mktime(mmpt.datetime.timetuple())) * 1000 + int(mmpt.datetime.microsecond / 1000)
            if tick_datetime - mmpt_datetime <= self.const_max_min_last_price_offset_sec * 1000:
                self.max_min_last_price_queue.appendleft(mmpt)
                self.max_min_last_price_queue_size += 1
                break

        if self.max_price_tick.last_price <= tick.last_price:
            self.max_price_tick = tick

    def build_last_price_5min(self):
        # 获取最近五分钟成交价中的最高点与最低点
        max_last_price = 0.0
        min_last_price = float('inf')
        lenth = self.max_min_last_price_queue_size
        while lenth > 0:
            mpt = self.max_min_last_price_queue.popleft()
            if mpt.last_price > max_last_price:
                max_last_price = mpt.last_price
            if mpt.last_price < min_last_price:
                min_last_price = mpt.last_price
            self.max_min_last_price_queue.append(mpt)
            lenth -= 1
        self.max_last_price_5min = max_last_price
        self.min_last_price_5min = min_last_price

    # 编辑交易相关变量
    def build_trade_parameter(self, trade: TradeData):
        # 交易相关参数重置
        if self.strategy_trade_state == 1:
            self.open_price = trade.price
        elif self.strategy_trade_state == 10 or self.strategy_trade_state == 20:
            self.tick_num_profit = 0
            self.tick_num_loss = 0

            # 平空仓 计算该空仓的开平仓回合的盈利情况
            round_profit_loss = (self.open_price - trade.price) * self.const_volume
            self.profit_now_value += round_profit_loss

            if self.profit_now_value > self.profit_max_value:
                self.profit_max_value = self.profit_now_value

        # 策略交易意图状态变更
        if self.strategy_trade_state == 1:
            self.strategy_trade_state = 5
        elif self.strategy_trade_state == 10:
            self.strategy_trade_state = 0
        elif self.strategy_trade_state == 20:
            self.strategy_trade_state = 0
        else:
            self.write_log("不正常的策略交易状态")

    # 判断策略是否启动
    def is_run_strategy(self, tick: TickData):
        return tick.last_price >= (self.mean_price_5s * 1.03)

    # 交易策略
    def trade_strategy(self, tick: TickData):
        # 当前不存在空仓
        if self.pos >= 0:
            if not self.strategy_running and self.is_run_strategy(tick):
                self.strategy_running = True

            if self.strategy_running:
                self.open(tick)
        else:
            # 获得盈利or亏损的行情tick数
            if self.open_price - tick.last_price > 0:
                self.tick_num_profit += 1
            else:
                self.tick_num_loss += 1

            # 止损判断
            if tick.last_price > self.open_price:
                self.close4stop_loss(tick)
            # 止盈判断
            else:
                self.close4stop_profit(tick)

    # 开仓逻辑
    def open(self, tick: TickData):
        self.strategy_trade_memo = str(self.pos) + "os"
        # 开仓条件一
        # length = self.trade_price_tick_queue_size
        # max_price_tick_3s: TickData = TickData
        # max_price_tick_3s.last_price = 0
        # while length > 0:
        #     t = self.trade_price_tick_queue.popleft()
        #     if t.last_price > max_price_tick_3s.last_price:
        #         max_price_tick_3s = t
        #     length -= 1
        #     self.trade_price_tick_queue.appendleft(t)
        # cond1 = tick.last_price < max_price_tick_3s.last_price
        # if cond1:
        #     memo += "-c1"
        # 开仓条件二
        bid_volume_total = \
            tick.bid_volume_1 + tick.bid_volume_2 + tick.bid_volume_3 + \
            tick.bid_volume_4 + tick.bid_volume_5
        ask_volume_total = \
            tick.ask_volume_1 + tick.ask_volume_2 + tick.ask_volume_3 + \
            tick.ask_volume_4 + tick.ask_volume_5
        cond2 = (bid_volume_total <= (ask_volume_total * self.const_ratio_long_short_open))
        if cond2:
            self.strategy_trade_memo += "-c2"
        if cond2:
            # 开空仓
            self.strategy_trade_memo += "-" + str(self.insert_order_num)
            self.add_trade_intention(tick.datetime, self.strategy_trade_memo)
            self.insert_order4open(tick)

    # 平仓-止盈逻辑
    def close4stop_profit(self, tick: TickData):
        self.strategy_trade_memo = str(self.pos) + "sp"
        # 止盈条件一
        bid_volume_total = \
            tick.bid_volume_1 + tick.bid_volume_2 + tick.bid_volume_3 + \
            tick.bid_volume_4 + tick.bid_volume_5
        ask_volume_total = \
            tick.ask_volume_1 + tick.ask_volume_2 + tick.ask_volume_3 + \
            tick.ask_volume_4 + tick.ask_volume_5
        cond1 = bid_volume_total >= ask_volume_total * self.const_ratio_long_short_stopprofit
        if cond1:
            self.strategy_trade_memo += "-c1"
        # 止盈条件二
        cond2 = \
            self.tick_num_profit > self.const_max_tick_num_profit and \
            (self.open_price - tick.last_price) < self.profit_max_value * self.const_max_backtest_ratio
        if cond2:
            self.strategy_trade_memo += "-c2"
        if cond1 or cond2:
            # 平空仓 止盈
            self.strategy_trade_memo += "-" + str(self.insert_order_num)
            self.add_trade_intention(tick.datetime, self.strategy_trade_memo)
            self.insert_order4stop_profit(tick)

    # 平仓-止损逻辑
    def close4stop_loss(self, tick: TickData):
        self.strategy_trade_memo = str(self.pos) + "sl"
        # 止损条件一
        cond1 = tick.last_price > self.max_price_tick.last_price
        if cond1:
            self.strategy_trade_memo += "-c1"
        # 止损条件二
        cond2 = self.tick_num_loss > self.const_max_tick_num_loss
        if cond2:
            self.strategy_trade_memo += "-c2"
        if cond1 or cond2:
            # 平空仓 止损
            self.strategy_trade_memo += "-" + str(self.insert_order_num)
            self.add_trade_intention(tick.datetime, self.strategy_trade_memo)
            self.insert_order4stop_loss(tick)

    def insert_order4open(self, tick: TickData):
        self.strategy_trade_state = 1
        self.insert_order_num += 1
        self.cancel_all()
        self.short(tick.ask_price_1 - self.price_tick * self.const_overprice, self.const_volume, memo=self.strategy_trade_memo)

    def insert_order4stop_profit(self, tick: TickData):
        self.strategy_trade_state = 20
        self.insert_order_num += 1
        self.cancel_all()
        self.cover(tick.bid_price_1 + self.price_tick * self.const_overprice, self.const_volume,
                   lock=False, memo=self.strategy_trade_memo)

    def insert_order4stop_loss(self, tick: TickData):
        self.strategy_trade_state = 10
        self.insert_order_num += 1
        self.cancel_all()
        self.cover(tick.bid_price_1 + self.price_tick * self.const_overprice, self.const_volume,
                   lock=False, memo=self.strategy_trade_memo)

