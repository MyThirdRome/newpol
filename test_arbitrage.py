#!/usr/bin/env python3
"""
Test arbitrage calculation logic
"""

from arbitrage_executor import ArbitrageExecutor

def test_stake_calculation():
    """Test stake calculation for equal profit"""
    print("=" * 60)
    print("Testing Arbitrage Stake Calculation")
    print("=" * 60)
    
    # Example: Dodgers $0.49, Phillies $0.48, Total $0.97
    price1 = 0.49
    price2 = 0.48
    bankroll = 100.0
    
    # Create executor (without real private key for testing)
    executor = ArbitrageExecutor(
        private_key="0x" + "0" * 64,  # Dummy key for testing
        bankroll=bankroll,
        min_profit_percent=1.0,
        auto_execute=False
    )
    
    # Calculate stakes
    stake1, stake2 = executor.calculate_stakes(price1, price2, bankroll)
    
    print(f"\nInput:")
    print(f"  Price 1 (Dodgers): ${price1:.2f}")
    print(f"  Price 2 (Phillies): ${price2:.2f}")
    print(f"  Total: ${price1 + price2:.2f}")
    print(f"  Bankroll: ${bankroll:.2f}")
    
    print(f"\nCalculated Stakes:")
    print(f"  Stake 1 (Dodgers): ${stake1:.2f}")
    print(f"  Stake 2 (Phillies): ${stake2:.2f}")
    print(f"  Total Staked: ${stake1 + stake2:.2f}")
    
    # Calculate profit for each outcome
    print(f"\nOutcome 1 (Dodgers win):")
    payout1 = stake1 / price1
    profit1 = payout1 - (stake1 + stake2)
    print(f"  Payout: ${payout1:.2f}")
    print(f"  Profit: ${profit1:.2f}")
    
    print(f"\nOutcome 2 (Phillies win):")
    payout2 = stake2 / price2
    profit2 = payout2 - (stake1 + stake2)
    print(f"  Payout: ${payout2:.2f}")
    print(f"  Profit: ${profit2:.2f}")
    
    # Calculate guaranteed profit
    guaranteed_profit = executor.calculate_profit(price1, price2, stake1, stake2)
    profit_percent = (guaranteed_profit / bankroll) * 100
    
    print(f"\nGuaranteed Profit:")
    print(f"  Amount: ${guaranteed_profit:.2f}")
    print(f"  Percentage: {profit_percent:.2f}%")
    
    # Verify
    print(f"\nVerification:")
    print(f"  Profit difference: ${abs(profit1 - profit2):.4f}")
    if abs(profit1 - profit2) < 0.01:
        print(f"  ✅ Profits are equal (within $0.01)")
    else:
        print(f"  ❌ Profits are NOT equal")
    
    print("\n" + "=" * 60)

def test_multiple_scenarios():
    """Test multiple arbitrage scenarios"""
    print("\nTesting Multiple Scenarios:")
    print("=" * 60)
    
    scenarios = [
        ("Dodgers vs Phillies", 0.49, 0.48, 0.97),
        ("O/U 7.5", 0.41, 0.54, 0.95),
        ("Spread -1.5", 0.60, 0.34, 0.94),
        ("Close to $1", 0.51, 0.50, 1.01),
    ]
    
    executor = ArbitrageExecutor(
        private_key="0x" + "0" * 64,
        bankroll=100.0,
        min_profit_percent=1.0,
        auto_execute=False
    )
    
    for name, price1, price2, total in scenarios:
        stake1, stake2 = executor.calculate_stakes(price1, price2, 100.0)
        profit = executor.calculate_profit(price1, price2, stake1, stake2)
        profit_percent = (profit / 100.0) * 100
        
        print(f"\n{name}:")
        print(f"  Prices: ${price1:.2f} + ${price2:.2f} = ${total:.2f}")
        print(f"  Stakes: ${stake1:.2f} + ${stake2:.2f}")
        print(f"  Profit: ${profit:.2f} ({profit_percent:.2f}%)")
        
        if total < 1.0:
            print(f"  ✅ Arbitrage opportunity!")
        else:
            print(f"  ❌ No arbitrage (total >= $1)")

if __name__ == "__main__":
    test_stake_calculation()
    test_multiple_scenarios()
