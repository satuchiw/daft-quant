from typing import Dict, Optional, List
import logging
import time

# Import xtquant
try:
    from xtquant import xttrader, xttype, xtconstant
except ImportError:
    print("Warning: xtquant not found. Mocking for development if needed.")

class OrderManager:
    """
    Wraps Mini-QMT order execution and provides simplified interface.
    """
    
    def __init__(self, xt_trader, account_id: str, logger: logging.Logger):
        self.xt_trader = xt_trader
        self.account_id = account_id
        self.logger = logger
        self.acc = xttype.StockAccount(account_id)

    def buy(self, symbol: str, price: float, quantity: int, strategy_name: str = "") -> str:
        """
        Place a buy order.
        
        Args:
            symbol: Stock code (e.g. '000001.SZ')
            price: Limit price. If 0 or -1, might imply market order depending on strategy type.
                   Mini-QMT usually requires price type.
                   We will use LATEST_PRICE (Limit) or MARKET depending on config.
                   Here we assume Limit order at 'price'.
            quantity: Number of shares (must be multiple of 100 for A-share buy)
        
        Returns:
            order_id: The order ID returned by QMT
        """
        return self._place_order(symbol, price, quantity, xtconstant.STOCK_BUY, strategy_name)

    def sell(self, symbol: str, price: float, quantity: int, strategy_name: str = "") -> str:
        """
        Place a sell order.
        """
        return self._place_order(symbol, price, quantity, xtconstant.STOCK_SELL, strategy_name)

    def _place_order(self, symbol: str, price: float, quantity: int, order_type: int, strategy_name: str) -> str:
        """
        Internal method to place order via xt_trader.
        """
        # Risk Check: Quantity must be positive
        if quantity <= 0:
            self.logger.warning(f"Order quantity must be positive: {quantity}")
            return ""
            
        # Place order asynchronously
        order_id = self.xt_trader.order_stock_async(
            self.acc,
            symbol,
            xtconstant.STOCK_BUY if order_type == xtconstant.STOCK_BUY else xtconstant.STOCK_SELL,
            quantity,
            xtconstant.FIX_PRICE, # Using Fix Price (Limit Order)
            price,
            strategy_name, 
            strategy_name 
        )
        
        action = "BUY" if order_type == xtconstant.STOCK_BUY else "SELL"
        self.logger.info(f"Placed {action} Order: {symbol} @ {price}, Qty: {quantity}, OrderID: {order_id}")
        
        return order_id

    def cancel_order(self, order_id: str):
        """
        Cancel an order by ID.
        """
        self.xt_trader.cancel_order_stock_async(self.acc, order_id)
        self.logger.info(f"Cancelled Order: {order_id}")

    def get_positions(self) -> List[xttype.StockPosition]:
        """
        Get current positions.
        """
        return self.xt_trader.query_stock_positions(self.acc)

    def get_asset(self) -> xttype.StockAsset:
        """
        Get account assets (Cash, Market Value).
        """
        return self.xt_trader.query_stock_asset(self.acc)
