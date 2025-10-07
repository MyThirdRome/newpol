#!/usr/bin/env python3
"""
Test 3-way arbitrage calculation (Team1, Draw, Team2)
"""

from arbitrage_executor import ArbitrageExecutor

def test_3way_calculation():
    """Test 3-way stake calculation for equal profit"""
    print("=" * 60)
    print("Testing 3-Way Arbitrage Stake Calculation")
    print("=" * 60)
    
    # Example: Nottingham $0.35, Draw $0.30, Chelsea $0.32, Total $0.97
    price1 = 0.35  # Nottingham win
    price2 = 0.30  # Draw
    price3 = 0.32  # Chelsea win
    bankroll = 11.0  # $11 max bet
    
    # Create executor
    executor = ArbitrageExecutor(
        private_key="0x" + "0" * 64,
        bankroll=bankroll,
        min_profit_percent=1.0,
        auto_execute=False
    )
    
    # Calculate stakes
    stake1, stake2, stake3 = executor.calculate_stakes_3way(price1, price2, price3, bankroll)
    
    total = price1 + price2 + price3
    
    print(f"\nInput:")
    print(f"  Price 1 (Nottingham): ${price1:.2f}")
    print(f"  Price 2 (Draw): ${price2:.2f}")
    print(f"  Price 3 (Chelsea): ${price3:.2f}")
    print(f"  Total: ${total:.2f}")
    print(f"  Bankroll: ${bankroll:.2f}")
    
    print(f"\nCalculated Stakes:")
    print(f"  Stake 1 (Nottingham): ${stake1:.2f}")
    print(f"  Stake 2 (Draw): ${stake2:.2f}")
    print(f"  Stake 3 (Chelsea): ${stake3:.2f}")
    print(f"  Total Staked: ${stake1 + stake2 + stake3:.2f}")
    
    # Calculate profit for each outcome
    print(f"\nOutcome 1 (Nottingham wins):")
    payout1 = stake1 / price1
    profit1 = payout1 - bankroll
    print(f"  Payout: ${payout1:.2f}")
    print(f"  Profit: ${profit1:.2f}")
    
    print(f"\nOutcome 2 (Draw):")
    payout2 = stake2 / price2
    profit2 = payout2 - bankroll
    print(f"  Payout: ${payout2:.2f}")
    print(f"  Profit: ${profit2:.2f}")
    
    print(f"\nOutcome 3 (Chelsea wins):")
    payout3 = stake3 / price3
    profit3 = payout3 - bankroll
    print(f"  Payout: ${payout3:.2f}")
    print(f"  Profit: ${profit3:.2f}")
    
    # Calculate guaranteed profit
    avg_profit = (profit1 + profit2 + profit3) / 3
    profit_percent = (avg_profit / bankroll) * 100
    
    print(f"\nGuaranteed Profit:")
    print(f"  Amount: ${avg_profit:.2f}")
    print(f"  Percentage: {profit_percent:.2f}%")
    
    # Verify
    print(f"\nVerification:")
    max_diff = max(abs(profit1 - profit2), abs(profit2 - profit3), abs(profit1 - profit3))
    print(f"  Max profit difference: ${max_diff:.4f}")
    if max_diff < 0.01:
        print(f"  ✅ Profits are equal (within $0.01)")
    else:
        print(f"  ❌ Profits are NOT equal")
    
    print("\n" + "=" * 60)

def test_multiple_3way_scenarios():
    """Test multiple 3-way scenarios"""
    print("\nTesting Multiple 3-Way Scenarios:")
    print("=" * 60)
    
    scenarios = [
        ("Good Opportunity", 0.35, 0.30, 0.32, 0.97),
        ("Better Opportunity", 0.30, 0.28, 0.35, 0.93),
        ("Best Opportunity", 0.28, 0.25, 0.37, 0.90),
        ("No Arbitrage", 0.40, 0.35, 0.30, 1.05),
    ]
    
    executor = ArbitrageExecutor(
        private_key="0x" + "0" * 64,
        bankroll=11.0,
        min_profit_percent=1.0,
        auto_execute=False
    )
    
    for name, p1, p2, p3, total in scenarios:
        stake1, stake2, stake3 = executor.calculate_stakes_3way(p1, p2, p3, 11.0)
        
        # Calculate profit
        payout1 = stake1 / p1
        profit = payout1 - 11.0
        profit_percent = (profit / 11.0) * 100
        
        print(f"\n{name}:")
        print(f"  Prices: ${p1:.2f} + ${p2:.2f} + ${p3:.2f} = ${total:.2f}")
        print(f"  Stakes: ${stake1:.2f} + ${stake2:.2f} + ${stake3:.2f}")
        print(f"  Profit: ${profit:.2f} ({profit_percent:.2f}%)")
        
        if total < 1.0:
            print(f"  ✅ 3-way arbitrage opportunity!")
        else:
            print(f"  ❌ No arbitrage (total >= $1)")

if __name__ == "__main__":
    test_3way_calculation()
    test_multiple_3way_scenarios()
