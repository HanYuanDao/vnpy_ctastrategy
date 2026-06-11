from vnpy_ctastrategy import (
    XinQiCtaTemplate,
    StopOrder,
    TickData,
    TradeData,
    OrderData,
)
from vnpy.trader.constant import Direction, Offset


class TestXinQiCtaStrategy(XinQiCtaTemplate):
    """
    Minimal XinQiCtaTemplate-based strategy for walking through
    open -> order callback -> trade callback -> stop-profit/stop-loss.
    """

    author = "OpenAI"

    fixed_size: int = 1
    profit_target: float = 2.0
    loss_target: float = 2.0

    last_tick_price: float = 0.0
    last_order_status: str = ""
    last_order_memo: str = ""
    last_trade_price: float = 0.0
    last_trade_memo: str = ""
    open_signal_count: int = 0
    stop_profit_signal_count: int = 0
    stop_loss_signal_count: int = 0
    round_reset_count: int = 0
    tmp_reset_count: int = 0

    parameters = [
        "fixed_size",
        "profit_target",
        "loss_target",
    ]
    variables = [
        "last_tick_price",
        "last_order_status",
        "last_order_memo",
        "last_trade_price",
        "last_trade_memo",
        "open_signal_count",
        "stop_profit_signal_count",
        "stop_loss_signal_count",
        "round_reset_count",
        "tmp_reset_count",
    ]

    def on_init(self) -> None:
        self.write_log("TestXinQiCtaStrategy initialized")

    def on_start(self) -> None:
        self.write_log("TestXinQiCtaStrategy started")

    def on_stop(self) -> None:
        self.write_log("TestXinQiCtaStrategy stopped")

    def on_stop_order(self, stop_order: StopOrder) -> None:
        _ = stop_order

    def build_quot_parameter(self) -> None:
        if self.tick_now is not None:
            self.last_tick_price = self.tick_now.last_price

    def build_order_parameter(self, order: OrderData) -> None:
        self.last_order_status = order.status.value
        self.last_order_memo = order.memo

    def build_trade_parameter(self, trade: TradeData) -> None:
        self.last_trade_price = trade.price
        self.last_trade_memo = trade.trade_memo

    def x_is_running_logic(self) -> bool:
        return True

    def x_judge_4_open(self) -> bool:
        return (
            self.tick_now is not None
            and self.pos == 0
            and self.trade_date_open is None
            and self.open_signal_count == 0
        )

    def x_judge_4_stop_loss(self) -> bool:
        if self.tick_now is None or self.trade_date_open is None or self.pos == 0:
            return False

        entry_price: float = self.trade_date_open.price

        if self.trade_date_open.direction == Direction.LONG:
            return self.tick_now.last_price <= entry_price - self.loss_target
        else:
            return self.tick_now.last_price >= entry_price + self.loss_target

    def x_judge_4_stop_profit(self) -> bool:
        if self.tick_now is None or self.trade_date_open is None or self.pos == 0:
            return False

        entry_price: float = self.trade_date_open.price

        if self.trade_date_open.direction == Direction.LONG:
            return self.tick_now.last_price >= entry_price + self.profit_target
        else:
            return self.tick_now.last_price <= entry_price - self.profit_target

    def x_insert_order_4_open(self) -> None:
        if self.tick_now is None:
            return

        self.open_signal_count += 1
        self.insert_order(
            Direction.LONG,
            Offset.OPEN,
            self.fixed_size,
            self.tick_now.ask_price_1,
            "test-open",
        )

    def x_insert_order_4_stop_loss(self) -> None:
        if self.tick_now is None or self.pos == 0:
            return

        self.stop_loss_signal_count += 1

        if self.pos > 0:
            self.insert_order(
                Direction.SHORT,
                Offset.CLOSE,
                abs(int(self.pos)),
                self.tick_now.bid_price_1,
                "test-stop-loss",
            )
        else:
            self.insert_order(
                Direction.LONG,
                Offset.CLOSE,
                abs(int(self.pos)),
                self.tick_now.ask_price_1,
                "test-stop-loss",
            )

    def x_insert_order_4_stop_profit(self) -> None:
        if self.tick_now is None or self.pos == 0:
            return

        self.stop_profit_signal_count += 1

        if self.pos > 0:
            self.insert_order(
                Direction.SHORT,
                Offset.CLOSE,
                abs(int(self.pos)),
                self.tick_now.bid_price_1,
                "test-stop-profit",
            )
        else:
            self.insert_order(
                Direction.LONG,
                Offset.CLOSE,
                abs(int(self.pos)),
                self.tick_now.ask_price_1,
                "test-stop-profit",
            )

    def reset_round_variable(self) -> None:
        self.round_reset_count += 1
        self.trade_direction = 0
        self.trade_date_open = None
        self.is_profit = False

    def reset_tmp_variable(self) -> None:
        self.tmp_reset_count += 1
        self.trade_direction = 0
        self.trade_date_open = None
        self.is_profit = False
