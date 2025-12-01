from typing import Dict, Any, Union, List
from .base_strategy import BaseStrategy

class RSIStrategy(BaseStrategy):
    def __init__(self, period: int = 14, overbought: float = 70.0, oversold: float = 30.0):
        super().__init__()
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
        self.prices: List[float] = []

    def on_init(self) -> None:
        print(f"Initializing RSIStrategy(period={self.period})")
        self.prices = []

    def on_bar(self, bar: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
        close_price = bar.get('close')
        if close_price is None:
            return "hold"
            
        self.prices.append(float(close_price))
        
        # We need at least period + 1 data points to calculate at least one change
        if len(self.prices) <= self.period:
            return "hold"
            
        # Keep history manageable
        if len(self.prices) > self.period * 5:
            self.prices.pop(0)
            
        rsi = self._calculate_rsi()
        
        if rsi is None:
            return "hold"
            
        if rsi < self.oversold:
            return "buy"
        elif rsi > self.overbought:
            return "sell"
            
        return "hold"

    def on_stop(self) -> None:
        print("Stopping RSIStrategy")

    def _calculate_rsi(self) -> Union[float, None]:
        if len(self.prices) < self.period + 1:
            return None
            
        # Calculate changes
        changes = []
        # We only need the last 'period' changes to calculate the initial RSI or smoothed RSI
        # Standard RSI uses a smoothed moving average (Wilder's Smoothing).
        # For simplicity here, we can use the simple average of gains/losses for the window
        # or implement the proper smoothing if possible.
        # Let's use the standard simple average for the first calculation and then smoothing?
        # Actually, recalculating from scratch on the last N items is essentially a Simple Moving Average RSI (Cutler's RSI).
        # Wilder's RSI requires maintaining the previous average gain/loss.
        
        # Let's implement a simple version based on the last 'period' intervals for independence.
        recent_prices = self.prices[-(self.period + 1):]
        for i in range(1, len(recent_prices)):
            changes.append(recent_prices[i] - recent_prices[i-1])
            
        gains = [c for c in changes if c > 0]
        losses = [abs(c) for c in changes if c < 0]
        
        avg_gain = sum(gains) / self.period
        avg_loss = sum(losses) / self.period
        
        if avg_loss == 0:
            return 100.0
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
