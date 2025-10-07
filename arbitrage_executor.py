#!/usr/bin/env python3
"""
Arbitrage Executor for Polymarket
Automatically executes arbitrage opportunities when detected
"""

import time
import logging
from typing import Dict, Tuple, Optional
from dataclasses import dataclass, asdict
import requests
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType
from py_clob_client.constants import POLYGON

logger = logging.getLogger('arbitrage_executor')

@dataclass
class ArbitrageOpportunity:
    """Arbitrage opportunity details"""
    event_title: str
    market_type: str
    side1_token_id: str
    side1_name: str
    side1_price: float
    side2_token_id: str
    side2_name: str
    side2_price: float
    total: float
    profit_percent: float
    timestamp: float

@dataclass
class ArbitrageExecution:
    """Arbitrage execution result"""
    opportunity: ArbitrageOpportunity
    bankroll: float
    stake1: float
    stake2: float
    order1_id: Optional[str]
    order2_id: Optional[str]
    success: bool
    error: Optional[str]
    timestamp: float

class ArbitrageExecutor:
    """Executes arbitrage trades automatically"""
    
    def __init__(self, private_key: str, bankroll: float, min_profit_percent: float = 1.0, 
                 auto_execute: bool = False, chain_id: int = POLYGON):
        """
        Initialize arbitrage executor
        
        Args:
            private_key: Ethereum private key for signing transactions
            bankroll: Total amount to use per arbitrage (in USDC)
            min_profit_percent: Minimum profit percentage to execute (default 1%)
            auto_execute: Enable automatic execution (default False for safety)
            chain_id: Blockchain network (POLYGON for mainnet)
        """
        self.private_key = private_key
        self.bankroll = bankroll
        self.min_profit_percent = min_profit_percent
        self.auto_execute = auto_execute
        self.chain_id = chain_id
        
        # Initialize Polymarket CLOB client
        try:
            self.client = ClobClient(
                host="https://clob.polymarket.com",
                key=private_key,
                chain_id=chain_id
            )
            logger.info("✅ Polymarket CLOB client initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize CLOB client: {e}")
            self.client = None
        
        # Track executions
        self.executions = []
        self.total_profit = 0.0
        self.successful_trades = 0
        self.failed_trades = 0
    
    def calculate_stakes(self, price1: float, price2: float, bankroll: float) -> Tuple[float, float]:
        """
        Calculate optimal stakes for equal profit on both outcomes (2-way)
        
        Args:
            price1: Price of side 1 (e.g., 0.49)
            price2: Price of side 2 (e.g., 0.48)
            bankroll: Total amount to stake
            
        Returns:
            (stake1, stake2) - Stakes for each side
        """
        # Correct formula for equal profit:
        # We want: stake1/price1 - total_stake = stake2/price2 - total_stake
        # This simplifies to: stake1/price1 = stake2/price2
        # And: stake1 + stake2 = bankroll
        # Solution: stake1 = bankroll * price1 / (price1 + price2)
        #           stake2 = bankroll * price2 / (price1 + price2)
        
        total_price = price1 + price2
        stake1 = bankroll * price1 / total_price
        stake2 = bankroll * price2 / total_price
        
        return stake1, stake2
    
    def calculate_stakes_3way(self, price1: float, price2: float, price3: float, 
                              bankroll: float) -> Tuple[float, float, float]:
        """
        Calculate optimal stakes for equal profit on all three outcomes (3-way)
        
        Args:
            price1: Price of outcome 1 (e.g., Team1 win)
            price2: Price of outcome 2 (e.g., Draw)
            price3: Price of outcome 3 (e.g., Team2 win)
            bankroll: Total amount to stake
            
        Returns:
            (stake1, stake2, stake3) - Stakes for each outcome
        """
        # For 3-way arbitrage with equal profit:
        # stake1/price1 = stake2/price2 = stake3/price3
        # stake1 + stake2 + stake3 = bankroll
        # Solution: stake_i = bankroll * price_i / (price1 + price2 + price3)
        
        total_price = price1 + price2 + price3
        stake1 = bankroll * price1 / total_price
        stake2 = bankroll * price2 / total_price
        stake3 = bankroll * price3 / total_price
        
        return stake1, stake2, stake3
    
    def calculate_profit(self, price1: float, price2: float, stake1: float, stake2: float) -> float:
        """
        Calculate guaranteed profit from arbitrage
        
        Args:
            price1: Price of side 1
            price2: Price of side 2
            stake1: Stake on side 1
            stake2: Stake on side 2
            
        Returns:
            Guaranteed profit amount
        """
        # Payout if side 1 wins
        payout1 = stake1 / price1
        profit1 = payout1 - (stake1 + stake2)
        
        # Payout if side 2 wins
        payout2 = stake2 / price2
        profit2 = payout2 - (stake1 + stake2)
        
        # Should be approximately equal, return average
        return (profit1 + profit2) / 2
    
    def should_execute(self, total: float) -> bool:
        """
        Check if arbitrage opportunity should be executed
        
        Args:
            total: Total price of both sides
            
        Returns:
            True if should execute
        """
        if not self.auto_execute:
            return False
        
        if total >= 1.0:
            return False
        
        profit_percent = ((1.0 - total) / total) * 100
        
        if profit_percent < self.min_profit_percent:
            logger.info(f"⚠️ Profit {profit_percent:.2f}% below minimum {self.min_profit_percent}%")
            return False
        
        return True
    
    def place_order(self, token_id: str, side: str, price: float, size: float) -> Optional[str]:
        """
        Place an order on Polymarket
        
        Args:
            token_id: Token ID to trade
            side: 'BUY' or 'SELL'
            price: Price per share
            size: Number of shares
            
        Returns:
            Order ID if successful, None otherwise
        """
        if not self.client:
            logger.error("❌ CLOB client not initialized")
            return None
        
        try:
            # Create order arguments
            order_args = OrderArgs(
                token_id=token_id,
                price=price,
                size=size,
                side=side,
                order_type=OrderType.GTC  # Good Till Cancelled
            )
            
            # Place order
            response = self.client.create_order(order_args)
            
            if response and 'orderID' in response:
                order_id = response['orderID']
                logger.info(f"✅ Order placed: {order_id} ({side} {size} @ ${price})")
                return order_id
            else:
                logger.error(f"❌ Order failed: {response}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error placing order: {e}")
            return None
    
    def execute_arbitrage(self, opportunity: ArbitrageOpportunity) -> ArbitrageExecution:
        """
        Execute arbitrage trade
        
        Args:
            opportunity: Arbitrage opportunity to execute
            
        Returns:
            Execution result
        """
        logger.info(f"🎯 Executing arbitrage: {opportunity.event_title} ({opportunity.market_type})")
        logger.info(f"   Total: ${opportunity.total:.4f} | Profit: {opportunity.profit_percent:.2f}%")
        
        # Calculate stakes
        stake1, stake2 = self.calculate_stakes(
            opportunity.side1_price,
            opportunity.side2_price,
            self.bankroll
        )
        
        logger.info(f"   Stake 1 ({opportunity.side1_name}): ${stake1:.2f} @ ${opportunity.side1_price:.4f}")
        logger.info(f"   Stake 2 ({opportunity.side2_name}): ${stake2:.2f} @ ${opportunity.side2_price:.4f}")
        
        # Calculate expected profit
        profit = self.calculate_profit(
            opportunity.side1_price,
            opportunity.side2_price,
            stake1,
            stake2
        )
        logger.info(f"   Expected profit: ${profit:.2f}")
        
        # Execute orders
        order1_id = None
        order2_id = None
        success = False
        error = None
        
        try:
            # Place first order
            order1_id = self.place_order(
                token_id=opportunity.side1_token_id,
                side='BUY',
                price=opportunity.side1_price,
                size=stake1 / opportunity.side1_price  # Convert to shares
            )
            
            if not order1_id:
                raise Exception("Failed to place order 1")
            
            # Place second order
            order2_id = self.place_order(
                token_id=opportunity.side2_token_id,
                side='BUY',
                price=opportunity.side2_price,
                size=stake2 / opportunity.side2_price  # Convert to shares
            )
            
            if not order2_id:
                # Cancel first order if second fails
                logger.warning("⚠️ Order 2 failed, attempting to cancel order 1")
                try:
                    self.client.cancel_order(order1_id)
                except:
                    pass
                raise Exception("Failed to place order 2")
            
            success = True
            self.successful_trades += 1
            self.total_profit += profit
            logger.info(f"✅ Arbitrage executed successfully!")
            
        except Exception as e:
            error = str(e)
            self.failed_trades += 1
            logger.error(f"❌ Arbitrage execution failed: {error}")
        
        # Create execution record
        execution = ArbitrageExecution(
            opportunity=opportunity,
            bankroll=self.bankroll,
            stake1=stake1,
            stake2=stake2,
            order1_id=order1_id,
            order2_id=order2_id,
            success=success,
            error=error,
            timestamp=time.time()
        )
        
        self.executions.append(execution)
        return execution
    
    def get_stats(self) -> Dict:
        """Get execution statistics"""
        return {
            'total_executions': len(self.executions),
            'successful_trades': self.successful_trades,
            'failed_trades': self.failed_trades,
            'total_profit': round(self.total_profit, 2),
            'auto_execute': self.auto_execute,
            'bankroll': self.bankroll,
            'min_profit_percent': self.min_profit_percent
        }
