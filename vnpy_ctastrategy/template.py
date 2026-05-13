from datetime import datetime
from abc import ABC, abstractmethod
from copy import copy
from typing import Any, cast
from collections.abc import Callable

from vnpy.trader.constant import Interval, Direction, Offset, Status, Produce, Exchange, CtaTradeStat
from vnpy.trader.object import BarData, TickData, OrderData, TradeData
from vnpy.trader.utility import BarGenerator, ArrayManager

from .base import StopOrder, EngineType


class CtaTemplate(ABC):
    """"""

    author: str = ""
    parameters: list = []
    variables: list = []

    def __init__(
        self,
        cta_engine: Any,
        strategy_name: str,
        vt_symbol: str,
        setting: dict,
    ) -> None:
        """"""
        self.cta_engine: Any = cta_engine
        self.strategy_name: str = strategy_name
        self.vt_symbol: str = vt_symbol

        self.inited: bool = False
        self.trading: bool = False
        self.pos: float = 0

        # Copy a new variables list here to avoid duplicate insert when multiple
        # strategy instances are created with the same strategy class.
        self.variables = copy(self.variables)
        self.variables.insert(0, "inited")
        self.variables.insert(1, "trading")
        self.variables.insert(2, "pos")

        self.update_setting(setting)

    def update_setting(self, setting: dict) -> None:
        """
        Update strategy parameter wtih value in setting dict.
        """
        for name in self.parameters:
            if name in setting:
                setattr(self, name, setting[name])

    @classmethod
    def get_class_parameters(cls) -> dict:
        """
        Get default parameters dict of strategy class.
        """
        class_parameters: dict = {}
        for name in cls.parameters:
            class_parameters[name] = getattr(cls, name)
        return class_parameters

    def get_parameters(self) -> dict:
        """
        Get strategy parameters dict.
        """
        strategy_parameters: dict = {}
        for name in self.parameters:
            strategy_parameters[name] = getattr(self, name)
        return strategy_parameters

    def get_variables(self) -> dict:
        """
        Get strategy variables dict.
        """
        strategy_variables: dict = {}
        for name in self.variables:
            strategy_variables[name] = getattr(self, name)
        return strategy_variables

    def get_data(self) -> dict:
        """
        Get strategy data.
        """
        strategy_data: dict = {
            "strategy_name": self.strategy_name,
            "vt_symbol": self.vt_symbol,
            "class_name": self.__class__.__name__,
            "author": self.author,
            "parameters": self.get_parameters(),
            "variables": self.get_variables(),
        }
        return strategy_data

    @abstractmethod
    def on_init(self) -> None:
        """
        Callback when strategy is inited.
        """
        return

    def on_start(self) -> None:
        """
        Callback when strategy is started.
        """
        return

    def on_stop(self) -> None:
        """
        Callback when strategy is stopped.
        """
        return

    def on_tick(self, tick: TickData) -> None:
        """
        Callback of new tick data update.
        """
        return

    def on_bar(self, bar: BarData) -> None:
        """
        Callback of new bar data update.
        """
        return

    def on_trade(self, trade: TradeData) -> None:
        """
        Callback of new trade data update.
        """
        return

    def on_order(self, order: OrderData) -> None:
        """
        Callback of new order data update.
        """
        return

    def on_stop_order(self, stop_order: StopOrder) -> None:
        """
        Callback of stop order update.
        """
        return

    def buy(
        self,
        price: float,
        volume: float,
        stop: bool = False,
        lock: bool = False,
        net: bool = False,
        memo: str = "",
    ) -> list:
        """
        Send buy order to open a long position.
        """
        return self.send_order(
            Direction.LONG,
            Offset.OPEN,
            price,
            volume,
            stop,
            lock,
            net,
            memo,
        )

    def sell(
        self,
        price: float,
        volume: float,
        stop: bool = False,
        lock: bool = False,
        net: bool = False,
        memo: str = "",
    ) -> list:
        """
        Send sell order to close a long position.
        """
        return self.send_order(
            Direction.SHORT,
            Offset.CLOSE,
            price,
            volume,
            stop,
            lock,
            net,
            memo,
        )

    def short(
        self,
        price: float,
        volume: float,
        stop: bool = False,
        lock: bool = False,
        net: bool = False,
        memo: str = "",
    ) -> list:
        """
        Send short order to open as short position.
        """
        return self.send_order(
            Direction.SHORT,
            Offset.OPEN,
            price,
            volume,
            stop,
            lock,
            net,
            memo,
        )

    def cover(
        self,
        price: float,
        volume: float,
        stop: bool = False,
        lock: bool = False,
        net: bool = False,
        memo: str = "",
    ) -> list:
        """
        Send cover order to close a short position.
        """
        return self.send_order(
            Direction.LONG,
            Offset.CLOSE,
            price,
            volume,
            stop,
            lock,
            net,
            memo,
        )

    def add_trade_intention(self, dt: datetime, memo: str) -> None:
        """
        Record strategy trade intention in engine.
        """
        self.cta_engine.add_trade_intention(dt, memo)

    def send_order(
        self,
        direction: Direction,
        offset: Offset,
        price: float,
        volume: float,
        stop: bool = False,
        lock: bool = False,
        net: bool = False,
        memo: str = "",
    ) -> list:
        """
        Send a new order.
        """
        if self.trading:
            vt_orderids: list = self.cta_engine.send_order(
                self, direction, offset, price, volume, stop, lock, net, memo
            )
            return vt_orderids
        else:
            return []

    def cancel_order(self, vt_orderid: str) -> None:
        """
        Cancel an existing order.
        """
        if self.trading:
            self.cta_engine.cancel_order(self, vt_orderid)

    def cancel_all(self) -> None:
        """
        Cancel all orders sent by strategy.
        """
        if self.trading:
            self.cta_engine.cancel_all(self)

    def write_log(self, msg: str) -> None:
        """
        Write a log message.
        """
        self.cta_engine.write_log(msg, self)

    def get_engine_type(self) -> EngineType:
        """
        Return whether the cta_engine is backtesting or live trading.
        """
        return cast(EngineType, self.cta_engine.get_engine_type())

    def get_pricetick(self) -> float:
        """
        Return pricetick data of trading contract.
        """
        return cast(float, self.cta_engine.get_pricetick(self))

    def get_size(self) -> int:
        """
        Return size data of trading contract.
        """
        return cast(int, self.cta_engine.get_size(self))

    def load_bar(
        self,
        days: int,
        interval: Interval = Interval.MINUTE,
        callback: Callable | None = None,
        use_database: bool = False
    ) -> None:
        """
        Load historical bar data for initializing strategy.
        """
        if not callback:
            callback = self.on_bar

        bars: list[BarData] = self.cta_engine.load_bar(
            self.vt_symbol,
            days,
            interval,
            callback,
            use_database
        )

        for bar in bars:
            callback(bar)

    def load_tick(self, days: int) -> None:
        """
        Load historical tick data for initializing strategy.
        """
        ticks: list[TickData] = self.cta_engine.load_tick(self.vt_symbol, days, self.on_tick)

        for tick in ticks:
            self.on_tick(tick)

    def put_event(self) -> None:
        """
        Put an strategy data event for ui update.
        """
        if self.inited:
            self.cta_engine.put_strategy_event(self)

    def send_email(self, msg: str) -> None:
        """
        Send email to default receiver.
        """
        if self.inited:
            self.cta_engine.send_email(msg, self)

    def sync_data(self) -> None:
        """
        Sync strategy variables value into disk storage.
        """
        if self.trading:
            self.cta_engine.sync_strategy_data(self)


class XinQiCtaTemplate(CtaTemplate):
    """
    XinQi 按照自己的交易规则定义的CTA策略
    规则和约定如下：
        1。 把临近的多、空方向的报单计作一个回合。当多、空报单手数一致时认为回合结束。
        2。 不会追加持仓，在一次开仓完整之后一定会等待回合完成之后再进行开仓操作。
    """
    author: str = "Xin Qi Technical Corporation"

    const_flag_close_mode: str = "lock"
    const_close_round_mode: str = "lock"

    def __init__(
        self,
        cta_engine: Any,
        strategy_name: str,
        vt_symbol: str,
        setting: dict,
    ) -> None:
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.tick_now: TickData | None = None
        self.tick_pre: TickData | None = None
        # 判断当前开仓持仓对象 在回合开始时赋值 在回合结束时置为None
        self.trade_date_open: TradeData | None = None
        # 判断是否盈利 在回合开始后新的行情数据进来时赋值 在回合结束时置为None
        self.is_profit: bool | None = None
        # 表明当前的报单是否已经成交
        self.insert_order_finish: bool = True

        # 获取到合约对应的交易所信息
        self.exchange: Exchange = Produce.get_product(vt_symbol).exchange
        # 交易方向
        # 0为初始状态 1为多 2为空
        self.trade_direction = 0
        # 策略交易的状态，使用 CtaTradeStat 表达。
        self.strategy_trade_state: CtaTradeStat = CtaTradeStat.INACTIVE

    def on_tick(self, tick: TickData) -> None:
        self.tick_now = tick

        # 剔除非交易时间行情
        if self.tick_now.datetime.hour <= 8 or 16 <= self.tick_now.datetime.hour < 21:
            return

        # 判断当前行情数据是否跨天
        if self.tick_pre is not None:
            current_trade_day: str = self.get_trade_day(self.tick_now)
            previous_trade_day: str = self.get_trade_day(self.tick_pre)
            if current_trade_day != previous_trade_day:
                self.strategy_trade_state = CtaTradeStat.INACTIVE
                self.reset_tmp_variable()

        # 在持仓状态下 算出当前的盈亏情况
        if self.trade_date_open is not None:
            if ((self.trade_date_open.direction.LONG and self.trade_date_open.price > self.tick_now.last_price)
                    or (self.trade_date_open.direction.SHORT and self.trade_date_open.price < self.tick_now.last_price)):
                self.is_profit = True
            else:
                self.is_profit = False

        self.handle_trade_process()
        self.tick_pre = self.tick_now

    def get_trade_day(self, tick: TickData) -> str:
        trade_day: Any = getattr(tick, "tradDay", "")
        if trade_day:
            return str(trade_day)
        return tick.datetime.date().isoformat()

    def handle_trade_process(self) -> None:
        """ 处理交易相关的逻辑 """
        if self.is_sleep_time():
            self.close_market()

        self.build_quot_parameter()

        if self.is_running_logic():
            self.handle_trade_strategy()

    def close_market(self) -> None:
        """ 收盘的操作 """
        self.write_log("收盘前进行强制平仓")
        self.force_close4normal()

    def handle_trade_strategy(self) -> None:
        """
        根据当前策略状态以及不同的标签进行策略状态的变迁
        这个状态里不进行任何参数的赋值 只进行状态的变迁已经对应状态绑定的方法的触发
        """
        if self.strategy_trade_state in {
            CtaTradeStat.INACTIVE,
            CtaTradeStat.OPENING,
            CtaTradeStat.CLEANING_CONFIRMED,
        }:
            self.x_judge4open()
        elif self.strategy_trade_state in (
                CtaTradeStat.HOLDING, CtaTradeStat.STOP_LOSSING, CtaTradeStat.STOP_PROFITING) :
            if self.is_profit is not None:
                if self.is_profit:
                    self.x_judge4stop_profit()
                    if self.strategy_trade_state == CtaTradeStat.STOP_PROFITING:
                        self.x_insert_order4stop_profit()
                else:
                    self.x_judge4stop_loss()
                    if self.strategy_trade_state == CtaTradeStat.STOP_LOSSING:
                        self.x_insert_order4stop_loss()

        if self.insert_order_finish:
            if self.strategy_trade_state == CtaTradeStat.STOP_LOSSING:
                self.x_insert_order4stop_loss()
            elif self.strategy_trade_state == CtaTradeStat.STOP_PROFITING:
                self.x_insert_order4stop_profit()
        else:
            if self.strategy_trade_state == CtaTradeStat.OPENING:
                self.x_insert_order4open()

    def on_order(self, order: OrderData) -> None:
        self.insert_order_finish = False
        self.build_order_parameter(order)
        self.put_event()

    def on_trade(self, trade: TradeData) -> None:
        self.insert_order_finish = False
        self.is_profit = None
        self.trade_date_open = None

        if self.strategy_trade_state == CtaTradeStat.OPENING:
            self.strategy_trade_state = CtaTradeStat.HOLDING
            self.insert_order_finish = True
            self.trade_date_open = trade
        elif self.strategy_trade_state in {
            CtaTradeStat.STOP_LOSSING,
            CtaTradeStat.STOP_PROFITING,
        }:
            self.strategy_trade_state = CtaTradeStat.INACTIVE
        elif self.strategy_trade_state == CtaTradeStat.HOLDING:
            self.insert_order4force_close(trade_memo="state error")
        else:
            self.write_log(f"func 'on_order' get an error strategy_trade_state{self.strategy_trade_state}")

        self.build_trade_parameter(trade)
        self.put_event()

    @abstractmethod
    def build_quot_parameter(self) -> None:
        pass

    @abstractmethod
    def build_order_parameter(self, order: OrderData) -> None:
        pass

    @abstractmethod
    def build_trade_parameter(self, trade: TradeData) -> None:
        pass

    @abstractmethod
    def is_running_logic(self) -> bool:
        """
        可以定制额外的暂停逻辑
        是程序不进入到开仓、止盈、止损的状态判断里
        """
        pass

    @abstractmethod
    def x_judge4open(self) -> None:
        """
        判断是否将策略状态改为开仓状态（self.strategy_trade_state = CtaTradeStat.OPENING）
        该方法中只能对self.strategy_trade_state进行设置 不能对其他参数进行设置
        """
        pass

    @abstractmethod
    def x_judge4stop_loss(self) -> None:
        """
        判断是否将策略状态改为止损状态（self.strategy_trade_state = CtaTradeStat.STOP_LOSSING）
        该方法中只能对self.strategy_trade_state进行设置 不能对其他参数进行设置
        """
        pass

    @abstractmethod
    def x_judge4stop_profit(self) -> None:
        """
        判断是否将策略状态改为止盈状态（self.strategy_trade_state = CtaTradeStat.STOP_PROFITING）
        该方法中只能对self.strategy_trade_state进行设置 不能对其他参数进行设置
        """
        pass

    @abstractmethod
    def x_insert_order4open(self) -> None:
        """ 调用insert_order进行开仓时候的报单 """
        pass

    @abstractmethod
    def x_insert_order4stop_loss(self) -> None:
        """ 调用insert_order进行止损平仓时候的报单 """
        pass

    @abstractmethod
    def x_insert_order4stop_profit(self) -> None:
        """ 调用insert_order进行止盈平仓时候的报单 """
        pass

    def insert_order4force_close(self, trade_memo: str) -> None:
        if self.tick_now is None:
            return

        self.insert_order(
            self.const_flag_close_mode == self.const_close_round_mode,
            self.pos < 0,
            abs(int(self.pos)),
            self.tick_now.ask_price_1 if self.pos < 0 else self.tick_now.bid_price_1,
            trade_memo
        )

    def force_close4normal(self) -> None:
        """ 正常地强制平仓 """
        if self.strategy_trade_state not in {
            CtaTradeStat.SLEEPING,
            CtaTradeStat.CLEANING_FIRST,
            CtaTradeStat.CLEANING_CONFIRMED,
        }:
            self.write_log("量化程序转为休眠状态")
            self.write_log("量化程序开始强制平仓")
            self.strategy_trade_state = CtaTradeStat.SLEEPING

        self.cancel_all()

        if self.pos != 0 and self.tick_now is not None:
            self.insert_order4force_close(trade_memo="force close when close")
        elif self.strategy_trade_state == CtaTradeStat.CLEANING_FIRST:
            self.strategy_trade_state = CtaTradeStat.CLEANING_CONFIRMED
            self.write_log("再次校验强制平仓时已无多余持仓")
        else:
            self.strategy_trade_state = CtaTradeStat.CLEANING_FIRST
            self.write_log("初次校验强制平仓时已无多余持仓")

    @abstractmethod
    def reset_tmp_variable(self) -> None:
        """ 重置跨交易日的相关参数的状态"""
        pass

    def is_sleep_time(self) -> bool:
        """ 判断是否需要休眠
        """
        # TODO Jason Han：需要根据不同的合约区别收盘时间
        if self.tick_now is None:
            return False

        return (
            self.tick_now.datetime.hour == 14
            and self.tick_now.datetime.minute == 59
            and self.tick_now.datetime.second >= 55
        ) or (
            self.tick_now.datetime.hour == 22
            and self.tick_now.datetime.minute == 59
            and self.tick_now.datetime.second >= 55
        )

    def insert_order(
        self,
        is_lock: bool,
        is_long: bool,
        volume: int,
        price: float,
        trade_memo: str,
    ) -> None:
        _ = trade_memo

        if is_lock:
            if is_long:
                self.buy(price, volume, lock=True, memo=trade_memo)
            else:
                self.cover(price, volume, lock=True, memo=trade_memo)
        else:
            if is_long:
                self.buy(price, volume, net=True, memo=trade_memo)
            else:
                self.cover(price, volume, net=True, memo=trade_memo)


class XinQiCtaTemplateBar(CtaTemplate):
    author: str = "Xin Qi Technical Corporation"
    const_flag_close_mode: str = "lock"
    const_close_round_mode: str = "lock"
    const_price_tick: float = 0
    parameters: list = [
        "const_close_round_mode",
        "const_price_tick",
    ]

    no_trade_tick_num: int = 0
    is_insert_order: bool = False
    order_open_price: float = 0
    strategy_trade_memo: str = ""
    trade_direction: int = 0
    variables: list = [
        "is_insert_order",
        "order_open_price",
        "strategy_trade_memo",
        "trade_direction",
    ]

    def __init__(
        self,
        cta_engine: Any,
        strategy_name: str,
        vt_symbol: str,
        setting: dict,
    ) -> None:
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg: BarGenerator = BarGenerator(self.on_bar)
        self.tick_now: TickData | None = None
        self.bar_now: BarData | None = None

    def on_init(self) -> None:
        self.write_log("策略初始化")
        self.reset_tmp_variable()
        self.on_xq_init()

    @abstractmethod
    def on_xq_init(self) -> None:
        pass

    def on_start(self) -> None:
        self.is_insert_order = False
        self.write_log("策略启动")

        self.const_price_tick = self.get_pricetick()
        self.on_xq_start()

    @abstractmethod
    def on_xq_start(self) -> None:
        pass

    def on_stop(self) -> None:
        self.write_log("策略停止")
        self.on_xq_stop()

    @abstractmethod
    def on_xq_stop(self) -> None:
        pass

    def on_tick(self, tick: TickData) -> None:
        self.tick_now = tick

        if self.is_insert_order:
            if self.no_trade_tick_num > 0:
                self.no_trade_tick_num -= 1
            else:
                self.cancel_all()

        if self.is_relax(tick):
            return

        self.bg.update_tick(tick)
        self.build_tick_parameter(tick)

    @abstractmethod
    def build_tick_parameter(self, tick: TickData) -> None:
        pass

    def on_bar(self, bar: BarData) -> None:
        self.bg.update_bar(bar)
        self.bar_now = bar
        self.build_bar_parameter(bar)

    @abstractmethod
    def build_bar_parameter(self, bar: BarData) -> None:
        pass

    def on_order(self, order: OrderData) -> None:
        if order.status in {Status.CANCELLED, Status.REJECTED}:
            self.is_insert_order = False

        self.build_order_parameter(order)

    @abstractmethod
    def build_order_parameter(self, order: OrderData) -> None:
        pass

    def on_trade(self, trade: TradeData) -> None:
        if self.is_insert_order:
            self.is_insert_order = False

        self.order_open_price = trade.price
        self.build_trade_parameter(trade)

    @abstractmethod
    def build_trade_parameter(self, trade: TradeData) -> None:
        pass

    @staticmethod
    def put_array_manager(am: ArrayManager, bar: BarData) -> bool:
        am.update_bar(bar)
        return am.inited

    def xq_buy(self, price: float, volume: float, memo: str) -> None:
        self.strategy_trade_memo = memo

        if not self.is_insert_order and self.trading:
            self.is_insert_order = True
            if self.is_close_mode(self.const_close_round_mode):
                self.buy(price, volume, lock=True, memo=memo)
            else:
                self.buy(price, volume, net=True, memo=memo)

    def xq_short(self, price: float, volume: float, memo: str) -> None:
        self.strategy_trade_memo = memo

        if not self.is_insert_order and self.trading:
            self.is_insert_order = True
            if self.is_close_mode(self.const_close_round_mode):
                self.short(price, volume, lock=True, memo=memo)
            else:
                self.short(price, volume, net=True, memo=memo)

    def xq_sell(self, price: float, volume: float, memo: str) -> None:
        self.strategy_trade_memo = memo

        if not self.is_insert_order and self.trading:
            self.is_insert_order = True
            if self.is_close_mode(self.const_close_round_mode):
                self.sell(price, volume, lock=True, memo=memo)
            else:
                self.sell(price, volume, net=True, memo=memo)

    def xq_cover(self, price: float, volume: float, memo: str) -> None:
        self.strategy_trade_memo = memo

        if not self.is_insert_order and self.trading:
            self.is_insert_order = True
            if self.is_close_mode(self.const_close_round_mode):
                self.cover(price, volume, lock=True, memo=memo)
            else:
                self.cover(price, volume, net=True, memo=memo)

    @staticmethod
    def is_close_mode(round_mode: str) -> bool:
        return XinQiCtaTemplateBar.const_flag_close_mode == round_mode

    @abstractmethod
    def reset_tmp_variable(self) -> None:
        pass

    @staticmethod
    def is_relax(tick: TickData) -> bool:
        return 3 < tick.datetime.hour < 9 or 15 <= tick.datetime.hour < 21


class CtaSignal(ABC):
    """"""

    def __init__(self) -> None:
        """"""
        self.signal_pos = 0

    def on_tick(self, tick: TickData) -> None:
        """
        Callback of new tick data update.
        """
        return

    @abstractmethod
    def on_bar(self, bar: BarData) -> None:
        """
        Callback of new bar data update.
        """
        return

    def set_signal_pos(self, pos: int) -> None:
        """"""
        self.signal_pos = pos

    def get_signal_pos(self) -> Any:
        """"""
        return self.signal_pos


class TargetPosTemplate(CtaTemplate):
    """"""
    tick_add = 1

    last_tick: TickData | None = None
    last_bar: BarData | None = None
    target_pos = 0

    def __init__(
        self,
        cta_engine: Any,
        strategy_name: str,
        vt_symbol: str,
        setting: dict
    ) -> None:
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.active_orderids: list[str] = []
        self.cancel_orderids: list[str] = []

        self.variables.append("target_pos")

    def on_tick(self, tick: TickData) -> None:
        """
        Callback of new tick data update.
        """
        self.last_tick = tick

    def on_bar(self, bar: BarData) -> None:
        """
        Callback of new bar data update.
        """
        self.last_bar = bar

    def on_order(self, order: OrderData) -> None:
        """
        Callback of new order data update.
        """
        vt_orderid: str = order.vt_orderid

        if not order.is_active():
            if vt_orderid in self.active_orderids:
                self.active_orderids.remove(vt_orderid)

            if vt_orderid in self.cancel_orderids:
                self.cancel_orderids.remove(vt_orderid)

    def check_order_finished(self) -> bool:
        """"""
        if self.active_orderids:
            return False
        else:
            return True

    def set_target_pos(self, target_pos: int) -> None:
        """"""
        self.target_pos = target_pos
        self.trade()

    def trade(self) -> None:
        """"""
        if not self.check_order_finished():
            self.cancel_old_order()
        else:
            self.send_new_order()

    def cancel_old_order(self) -> None:
        """"""
        for vt_orderid in self.active_orderids:
            if vt_orderid not in self.cancel_orderids:
                self.cancel_order(vt_orderid)
                self.cancel_orderids.append(vt_orderid)

    def send_new_order(self) -> None:
        """"""
        pos_change = self.target_pos - self.pos
        if not pos_change:
            return

        long_price: float = 0
        short_price: float = 0

        if self.last_tick:
            if pos_change > 0:
                long_price = self.last_tick.ask_price_1 + self.tick_add
                if self.last_tick.limit_up:
                    long_price = min(long_price, self.last_tick.limit_up)
            else:
                short_price = self.last_tick.bid_price_1 - self.tick_add
                if self.last_tick.limit_down:
                    short_price = max(short_price, self.last_tick.limit_down)

        elif self.last_bar:
            if pos_change > 0:
                long_price = self.last_bar.close_price + self.tick_add
            else:
                short_price = self.last_bar.close_price - self.tick_add

        if self.get_engine_type() == EngineType.BACKTESTING:
            if pos_change > 0:
                vt_orderids: list[str] = self.buy(long_price, abs(pos_change))
            else:
                vt_orderids = self.short(short_price, abs(pos_change))
            self.active_orderids.extend(vt_orderids)

        else:
            if self.active_orderids:
                return

            if pos_change > 0:
                if self.pos < 0:
                    if pos_change < abs(self.pos):
                        vt_orderids = self.cover(long_price, pos_change)
                    else:
                        vt_orderids = self.cover(long_price, abs(self.pos))
                else:
                    vt_orderids = self.buy(long_price, abs(pos_change))
            else:
                if self.pos > 0:
                    if abs(pos_change) < self.pos:
                        vt_orderids = self.sell(short_price, abs(pos_change))
                    else:
                        vt_orderids = self.sell(short_price, abs(self.pos))
                else:
                    vt_orderids = self.short(short_price, abs(pos_change))
            self.active_orderids.extend(vt_orderids)
