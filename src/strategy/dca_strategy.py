"""
Dollar Cost Averaging (DCA) Strategy
Invests a fixed amount at regular intervals regardless of price.
"""
from typing import Dict, Any, Union
from .base_strategy import BaseStrategy


class DCAStrategy(BaseStrategy):
    """
    Weekly Dollar Cost Averaging Strategy.
    
    Buys a fixed cash amount every week, regardless of market conditions.
    This is a passive investment strategy that averages out entry prices over time.
    """
    
    def __init__(self, weekly_amount: float = 1000.0):
        """
        Args:
            weekly_amount: Fixed amount to invest each week (in currency units)
        """
        super().__init__()
        self.weekly_amount = weekly_amount
        self.last_week = None
        self.bars_processed = 0
    
    def on_init(self) -> None:
        print(f"Initializing DCAStrategy(weekly_amount={self.weekly_amount})")
        self.last_week = None
        self.bars_processed = 0
    
    def on_bar(self, bar: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
        self.bars_processed += 1
        dt = bar.get('datetime')
        
        if dt is None:
            return "hold"
        
        # Get ISO week number (1-52/53)
        current_week = dt.isocalendar()[1]
        current_year = dt.year
        week_key = (current_year, current_week)
        
        # Buy once per week (on first bar of each new week)
        if self.last_week != week_key:
            self.last_week = week_key
            # Return a signal with the fixed cash amount to invest
            return {
                "action": "buy",
                "cash_amount": self.weekly_amount
            }
        
        return "hold"
    
    def on_stop(self) -> None:
        print(f"Stopping DCAStrategy (processed {self.bars_processed} bars)")
