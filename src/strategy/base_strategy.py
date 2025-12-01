from abc import ABC, abstractmethod
from typing import Dict, Any, Union

class BaseStrategy(ABC):
    """
    Base class for all strategies.
    Strategies must be independent of the execution/backtest engine.
    They only generate signals based on input data.
    """

    def __init__(self):
        pass

    @abstractmethod
    def on_init(self) -> None:
        """
        Called when the strategy is initialized.
        Use this to set up parameters, indicators, etc.
        """
        pass

    @abstractmethod
    def on_bar(self, bar: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
        """
        Called on every new bar.
        
        Args:
            bar: A dictionary containing OHLCV data and datetime.
                 Expected keys: 'datetime', 'open', 'high', 'low', 'close', 'volume' (optional)
        
        Returns:
            Signal: "buy", "sell", "hold", or a custom signal dictionary.
        """
        pass

    @abstractmethod
    def on_stop(self) -> None:
        """
        Called when the strategy execution is stopped.
        Use this for cleanup or saving state.
        """
        pass
