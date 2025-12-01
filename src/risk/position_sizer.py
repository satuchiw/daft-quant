from dataclasses import dataclass
from typing import Optional


@dataclass
class PositionSizingConfig:
    """Configuration for position sizing.

    Notes
    -----
    - `method` controls the sizing logic:
        - "all_in": use legacy behavior (almost all cash, 99%).
        - "fixed_fraction": use a fixed fraction of current cash, but keep
          at least `min_cash_fraction` of *initial* capital as cash.
        - "fixed_cash": use a fixed cash amount per trade, while respecting
          `min_cash_fraction`.
    - Stop-loss based sizing / Kelly can hook into this later via
      `risk_per_share` and `max_risk_fraction`.
    """

    method: str = "all_in"              # 'all_in', 'fixed_fraction', 'fixed_cash'
    fraction: float = 0.6               # fraction of cash to allocate per trade (for fixed_fraction)
    fixed_cash: float = 20000.0         # fixed cash per trade (for fixed_cash)
    lot_size: int = 100                 # A-share standard lot size

    # Minimum cash to keep as a fraction of initial capital, e.g. 0.4 => keep 40% cash
    min_cash_fraction: float = 0.4

    # Placeholders for future risk-based sizing (stop-loss, Kelly, etc.)
    max_risk_fraction: float = 0.02     # max 2% of equity per trade (not used yet)
    use_stop_loss: bool = False         # reserved flag, not used yet


class PositionSizer:
    """Position sizing helper used by both backtest and live trading engines.

    This class does *not* enforce T+1 rules or broker-specific constraints;
    it only computes a desired quantity based on price, cash, and config.
    The caller (engine) is responsible for final checks.
    """

    def __init__(self, config: Optional[PositionSizingConfig] = None, initial_capital: float = 0.0):
        self.config = config or PositionSizingConfig()
        self.initial_capital = float(initial_capital)

    def _round_to_lot(self, qty: int) -> int:
        if qty <= 0:
            return 0
        return (qty // self.config.lot_size) * self.config.lot_size

    def size(self, price: float, cash_available: float, current_position: int = 0) -> int:
        """Return desired *buy* quantity.

        Parameters
        ----------
        price : float
            Execution price estimate.
        cash_available : float
            Current available cash.
        current_position : int
            Current position size (not used yet, but may be useful later).
        """
        if price <= 0 or cash_available <= 0:
            return 0

        method = self.config.method

        # Legacy behavior: nearly all-in (keep ~1% cash reserve for costs)
        if method == "all_in":
            max_qty = int((cash_available * 0.99) / price)
            return self._round_to_lot(max_qty)

        # Minimum cash reserve based on initial capital
        min_cash_to_keep = self.initial_capital * self.config.min_cash_fraction
        allocatable_cash = max(0.0, cash_available - min_cash_to_keep)
        if allocatable_cash <= 0:
            return 0

        if method == "fixed_fraction":
            trade_cash = allocatable_cash * self.config.fraction
        elif method == "fixed_cash":
            trade_cash = min(self.config.fixed_cash, allocatable_cash)
        else:
            # Unknown method -> fall back to no trade
            return 0

        if trade_cash <= 0:
            return 0

        max_qty = int(trade_cash / price)
        return self._round_to_lot(max_qty)
