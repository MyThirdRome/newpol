# Arbitrage Auto-Execution Guide

## ⚠️ IMPORTANT WARNING

**This feature automatically executes real trades with real money!**

- Only enable if you understand the risks
- Test with small amounts first
- Keep your private key secure
- Monitor executions closely

## How It Works

When the system detects a best match (total under $1.00), it:

1. **Calculates optimal stakes** for equal profit on both outcomes
2. **Places buy orders** on both sides simultaneously
3. **Guarantees profit** regardless of which side wins

### Example (2-Way):

**Dodgers $0.49 + Phillies $0.48 = $0.97**

With $11 bankroll:
- Stake on Dodgers: $5.56
- Stake on Phillies: $5.44
- **Guaranteed profit: $0.34** (3.09% return)

If Dodgers win: Payout $11.34 - Staked $11 = **$0.34 profit**  
If Phillies win: Payout $11.34 - Staked $11 = **$0.34 profit**

### Example (3-Way):

**Nottingham $0.35 + Draw $0.30 + Chelsea $0.32 = $0.97**

With $11 bankroll:
- Stake on Nottingham: $3.97
- Stake on Draw: $3.40
- Stake on Chelsea: $3.63
- **Guaranteed profit: $0.34** (3.09% return)

If Nottingham wins: Payout $11.34 - Staked $11 = **$0.34 profit**  
If Draw: Payout $11.34 - Staked $11 = **$0.34 profit**  
If Chelsea wins: Payout $11.34 - Staked $11 = **$0.34 profit**

## Configuration

Edit `config.py`:

```python
# Arbitrage Trading
ARBITRAGE_ENABLED = True  # Enable auto-trading
ARBITRAGE_PRIVATE_KEY = "0xYOUR_PRIVATE_KEY_HERE"  # Ethereum private key
ARBITRAGE_BANKROLL = 100.0  # Amount in USDC per trade
ARBITRAGE_MIN_PROFIT_PERCENT = 1.0  # Minimum 1% profit to execute
```

### Configuration Options:

- **ARBITRAGE_ENABLED**: Set to `True` to enable auto-execution
- **ARBITRAGE_PRIVATE_KEY**: Your Ethereum private key (KEEP SECRET!)
- **ARBITRAGE_BANKROLL**: Total USDC to use per arbitrage opportunity
- **ARBITRAGE_MIN_PROFIT_PERCENT**: Minimum profit percentage to execute

## Setup

### 1. Install Dependencies

```bash
pip install py-clob-client web3 eth-account
```

### 2. Get Your Private Key

From MetaMask or your Ethereum wallet:
1. Export your private key
2. **NEVER share it with anyone**
3. Store it securely

### 3. Fund Your Wallet

- Deposit USDC to your Polygon wallet
- Ensure you have enough for trades + gas fees
- Recommended: Start with small amounts for testing

### 4. Configure

```bash
cd /opt/polymarket-orderbook-monitor
nano config.py
```

Set:
```python
ARBITRAGE_ENABLED = True
ARBITRAGE_PRIVATE_KEY = "0xYOUR_KEY_HERE"
ARBITRAGE_BANKROLL = 50.0  # Start small!
ARBITRAGE_MIN_PROFIT_PERCENT = 2.0  # Higher threshold for safety
```

### 5. Restart

```bash
./stop.sh
./start.sh
```

## Monitoring

### Check Execution Stats

```bash
curl http://localhost:5001/api/arbitrage/stats
```

Returns:
```json
{
  "total_executions": 5,
  "successful_trades": 4,
  "failed_trades": 1,
  "total_profit": 15.45,
  "auto_execute": true,
  "bankroll": 100.0,
  "min_profit_percent": 1.0
}
```

### View Execution History

```bash
curl http://localhost:5001/api/arbitrage/executions
```

### Watch Logs

```bash
tail -f logs/app.log | grep -E "BEST MATCH|Executing arbitrage|executed"
```

## Safety Features

1. **Minimum Profit Threshold**: Won't execute if profit < configured %
2. **Automatic Stake Calculation**: Ensures equal profit on both outcomes
3. **Order Cancellation**: Cancels first order if second order fails
4. **Execution Logging**: All trades logged for audit trail
5. **Manual Override**: Can disable at any time in config

## Testing

Test the calculation logic without real trades:

**2-Way Markets (Team1 vs Team2):**
```bash
python3 test_arbitrage.py
```

**3-Way Markets (Team1, Draw, Team2):**
```bash
python3 test_3way_arbitrage.py
```

This shows:
- Stake calculations
- Expected profits
- Verification of equal profit on all outcomes

## Risk Management

### Recommended Settings for Beginners:

```python
ARBITRAGE_BANKROLL = 20.0  # Small amount
ARBITRAGE_MIN_PROFIT_PERCENT = 3.0  # Higher threshold
```

### For Experienced Traders:

```python
ARBITRAGE_BANKROLL = 500.0  # Larger amount
ARBITRAGE_MIN_PROFIT_PERCENT = 0.5  # Lower threshold
```

## Troubleshooting

### "CLOB client not initialized"
- Check your private key is correct
- Ensure it starts with "0x"
- Verify you have USDC in your wallet

### "Order failed"
- Check you have enough USDC balance
- Verify you have MATIC for gas fees
- Ensure prices haven't changed (slippage)

### "Profit below minimum"
- Opportunity didn't meet your profit threshold
- This is normal - system is protecting you
- Lower `ARBITRAGE_MIN_PROFIT_PERCENT` if desired

## Disabling Auto-Execution

To stop auto-trading:

```python
ARBITRAGE_ENABLED = False
```

Then restart:
```bash
./stop.sh && ./start.sh
```

The system will still detect and log opportunities, but won't execute trades.

## Security Best Practices

1. **Never commit private key to git**
2. **Use environment variables** for production
3. **Limit wallet funds** to what you're willing to risk
4. **Monitor regularly** for unexpected behavior
5. **Start small** and scale up gradually

## Support

For issues or questions:
- Check logs: `tail -f logs/app.log`
- Test calculations: `python3 test_arbitrage.py`
- Review executions: `curl http://localhost:5001/api/arbitrage/executions`

## Disclaimer

**Use at your own risk!**

- This is experimental software
- No guarantees of profit
- Market conditions can change rapidly
- You are responsible for all trades executed
- Always test with small amounts first
