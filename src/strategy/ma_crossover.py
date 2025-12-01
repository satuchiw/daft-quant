from typing import Dict, Any, Union, List
from .base_strategy import BaseStrategy

class MACrossoverStrategy(BaseStrategy):
    def __init__(self, short_window: int = 10, long_window: int = 30):
        super().__init__()
        self.short_window = short_window
        self.long_window = long_window
        self.prices: List[float] = []
        self.short_ma = 0.0
        self.long_ma = 0.0
        self.prev_short_ma = 0.0
        self.prev_long_ma = 0.0

    def on_init(self) -> None:
        print(f"Initializing MACrossoverStrategy(short={self.short_window}, long={self.long_window})")
        self.prices = []

    def on_bar(self, bar: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
        close_price = bar.get('close')
        
        if close_price is None:
            return "hold"

        self.prices.append(float(close_price))

        # Keep history size manageable, but enough for long_window
        if len(self.prices) > self.long_window + 1:
             self.prices.pop(0)

        if len(self.prices) < self.long_window:
            return "hold"

        # Calculate MAs
        # We use simple moving average here for simplicity
        current_prices = self.prices[-self.long_window:]
        self.long_ma = sum(current_prices) / self.long_window
        
        short_prices = self.prices[-self.short_window:]
        self.short_ma = sum(short_prices) / self.short_window

        # Store previous MAs to detect crossover
        # In a real implementation, we would need the previous step's MA or the previous bar's calculation.
        # Here, we can check if we have enough history to have a "previous" state.
        # If this is the first time we have enough data, we can't really detect a crossover yet, just state.
        
        signal = "hold"
        
        # We need at least one previous calculation to check for crossover
        # But since we recalculate from history list every time, 
        # we can simulate the "previous" MAs by looking at the list shifted by 1
        
        if len(self.prices) >= self.long_window + 1:
             prev_prices_long = self.prices[-(self.long_window+1):-1]
             prev_long_ma = sum(prev_prices_long) / self.long_window
             
             prev_prices_short = self.prices[-(self.short_window+1):-1]
             prev_short_ma = sum(prev_prices_short) / self.short_window
             
             # Golden Cross: Short MA crosses above Long MA
             if prev_short_ma <= prev_long_ma and self.short_ma > self.long_ma:
                 signal = "buy"
             # Death Cross: Short MA crosses below Long MA
             elif prev_short_ma >= prev_long_ma and self.short_ma < self.long_ma:
                 signal = "sell"
        
        return signal

    def on_stop(self) -> None:
        print("Stopping MACrossoverStrategy")
