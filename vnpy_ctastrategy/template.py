from datetime import datetime
from abc import ABC, abstractmethod
from copy import copy
from typing import Any, cast
from collections.abc import Callable

from vnpy.trader.constant import Interval, Direction, Offset
from vnpy.trader.object import BarData, TickData, OrderData, TradeData

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
        self.pos: int = 0

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
        memo: str = ""
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
            memo
        )

    def sell(
        self,
        price: float,
        volume: float,
        stop: bool = False,
        lock: bool = False,
        net: bool = False,
        memo: str = ""
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
            memo
        )

    def short(
        self,
        price: float,
        volume: float,
        stop: bool = False,
        lock: bool = False,
        net: bool = False,
        memo: str = ""
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
            memo
        )

    def cover(
        self,
        price: float,
        volume: float,
        stop: bool = False,
        lock: bool = False,
        net: bool = False,
        memo: str = ""
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
            memo
        )

    def send_order(
        self,
        direction: Direction,
        offset: Offset,
        price: float,
        volume: float,
        stop: bool = False,
        lock: bool = False,
        net: bool = False,
        memo: str = ""
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

    def add_trade_intention(self, dt: datetime, memo: str) -> None:
        """Record strategy trade intention through CTA engine."""
        self.cta_engine.add_trade_intention(dt, memo)

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
    # 声明作者
    author = "Xin Qi Technical Corporation"

    const_flag_close_mode = "lock"
    const_flag_insert_order_finish: bool = True

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        # 当前tick
        self.tick_now: TickData = None
        # 前一个tick
        self.tick_pre: TickData = None

        # 记录开仓时的交易对象
        self.trade_date_open: TradeData = None
        # 策略交易的状态
        # 0：不进行任何活动
        # 1：开始开仓
        # 5：已持仓
        # 10：开始止损
        # 20：开始止盈
        # 91: 转为休眠
        # 92: 首次清理持仓
        # 93: 确认持仓清理完毕
        self.strategy_trade_state = 0

    def on_tick(self, tick: TickData):
        self.tick_now = tick

        # 去除非交易时间的数据
        if self.tick_now.datetime.hour <= 8 or 16 < self.tick_now.datetime.hour < 21:
            return

        if self.tick_pre is not None \
                and self.tick_now.tradDay != self.tick_pre.tradDay:
            self.strategy_trade_state = 0
            self.reset_tmp_variable()

        self.handle_trade_process()

        self.tick_pre = self.tick_now

    def force_close4normal(self):
        if self.strategy_trade_state != 91 and self.strategy_trade_state != 92 and self.strategy_trade_state != 93:
            self.write_log("量化程序转为休眠状态")
            self.write_log("量化程序开始强制平仓")
            self.strategy_trade_state = 91
        self.cancel_all()
        if self.pos != 0:
            self.insert_order4force_close(trade_memo="force close when close")
        else:
            if self.strategy_trade_state == 92:
                self.strategy_trade_state = 93
                self.write_log("再次校验强制平仓时已无多余持仓")
            else:
                self.strategy_trade_state = 92
                self.write_log("初次校验强制平仓时已无多余持仓")

    def handle_trade_process(self):
        if self.is_sleep_time():
            self.force_close4normal()

        self.build_quot_parameter()

        if self.is_running_logic():
            self.handle_trade_strategy()

    def handle_trade_strategy(self):
        if self.strategy_trade_state == 0 or self.strategy_trade_state == 1 or self.strategy_trade_state == 93:
            self.open()
        elif self.strategy_trade_state == 5:
            self.close4stop_profit()
            self.close4stop_loss()
        elif self.strategy_trade_state == 10:
            self.close4stop_loss()
        elif self.strategy_trade_state == 20:
            self.close4stop_profit()

        """
        在此处应该要添加分析交易状态是否准确的方法
        以供从统计上判断策略对于行情走势判断的准确程度
        """

        if self.const_flag_insert_order_finish is True:
            if self.strategy_trade_state == 1:
                self.insert_order4open()
            elif self.strategy_trade_state == 10:
                self.insert_order4stop_loss()
            elif self.strategy_trade_state == 20:
                self.insert_order4stop_profit()

    def on_order(self, order: OrderData):
        self.const_flag_insert_order_finish = False
        self.build_order_parameter(order)
        self.put_event()

    def on_trade(self, trade: TradeData):
        self.const_flag_insert_order_finish = True
        if self.strategy_trade_state == 1:
            self.trade_date_open = trade
            self.strategy_trade_state == 5
        elif self.strategy_trade_state == 10:
            self.strategy_trade_state = 0
        elif self.strategy_trade_state == 20:
            self.strategy_trade_state = 0
        elif self.strategy_trade_state == 5:
            self.insert_order4force_close(trade_memo="state error")
        else:
            self.write_log("func 'on_order' get an error strategy_trade_state" + str(self.strategy_trade_state))

        self.build_trade_parameter(trade)
        self.put_event()

    @abstractmethod
    def build_quot_parameter(self):
        """ 处理行情参数

        Returns:

        """
        pass

    @abstractmethod
    def build_order_parameter(self, order: OrderData):
        """ 当报单成功时处理回调信息

        Args:
            order:

        Returns:

        """
        pass

    @abstractmethod
    def build_trade_parameter(self, trade: TradeData):
        """ 当订单成交时处理回调信息

        Args:
            trade:

        Returns:

        """
        pass

    @abstractmethod
    def is_running_logic(self):
        pass

    @abstractmethod
    def open(self):
        pass

    @abstractmethod
    def close4stop_loss(self):
        pass

    @abstractmethod
    def close4stop_profit(self):
        pass

    @abstractmethod
    def insert_order4open(self):
        pass

    @abstractmethod
    def insert_order4stop_loss(self):
        pass

    @abstractmethod
    def insert_order4stop_profit(self):
        pass

    def insert_order4force_close(self, trade_memo: str):
        self.insert_order(self.const_flag_close_mode.__eq__(self.const_close_round_mode),
                          self.pos < 0,
                          abs(self.pos),
                          self.tick_now.ask_price_1 if self.pos < 0 else self.tick_now.bid_price_1,
                          trade_memo)

    @abstractmethod
    def reset_tmp_variable(self):
        """ 处理跨交易日时需要重置的参数

        Returns:

        """
        pass

    def is_sleep_time(self):
        if (self.tick_now.datetime.hour == 14
            and self.tick_now.datetime.minute == 59
            and self.tick_now.datetime.second >= 55) \
                or (self.tick_now.datetime.hour == 22
                    and self.tick_now.datetime.minute == 59
                    and self.tick_now.datetime.second >= 55):
            return True
        else:
            return False

    def insert_order(self, is_lock: bool, is_long: bool, volume: int, price: float, trade_memo: str):
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

    last_tick: TickData = None
    last_bar: BarData = None
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

        long_price = 0
        short_price = 0

        if self.last_tick:
            if pos_change > 0:
                long_price = self.last_tick.ask_price_1 + self.tick_add
                if self.last_tick.limit_up:
                    long_price = min(long_price, self.last_tick.limit_up)
            else:
                short_price = self.last_tick.bid_price_1 - self.tick_add
                if self.last_tick.limit_down:
                    short_price = max(short_price, self.last_tick.limit_down)

        else:
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
