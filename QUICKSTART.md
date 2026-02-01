# 🚀 Quick Start Guide - Kalshi Trading Bot

## 📋 Pre-Flight Checklist

### Step 1: Setup Environment (5 minutes)

```powershell
# Navigate to project
cd "c:\Users\jgons\Agents\Kalshi Trading"

# Create virtual environment
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Get API Keys (10 minutes)

#### Kalshi API:
1. Go to https://kalshi.com
2. Create account (if needed)
3. Navigate to Settings → API
4. Generate API key pair
5. **Save both key and secret** (shown only once!)

#### NewsAPI (Optional):
1. Go to https://newsapi.org
2. Sign up for free account
3. Copy API key from dashboard

### Step 3: Configure Bot (2 minutes)

```powershell
# Copy template
cp .env.example .env

# Edit with your keys
notepad .env
```

**Fill in your `.env`:**
```env
KALSHI_API_KEY=kxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
KALSHI_API_SECRET=sxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
KALSHI_ENV=demo  # ⚠️ START WITH DEMO!
NEWS_API_KEY=nxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # Optional
```

### Step 4: Validate Setup (1 minute)

```powershell
# Run validation script
python setup_check.py
```

**Expected output:**
```
✅ Python 3.10+
✅ All dependencies installed
✅ .env file configured
✅ Configuration valid
```

### Step 5: Test API Connection (1 minute)

```powershell
# Test Kalshi API
python test_api.py
```

**Expected output:**
```
✅ Balance: $10,000.00  # Demo account
✅ Found 50+ markets
```

### Step 6: Run the Bot! 🎉

```powershell
# Start trading (sandbox mode)
python kalshi_bot.py
```

---

## 🎯 What to Expect

### First 5 Minutes:
- Bot scans all open Kalshi markets
- Calculates fair value for each
- Looks for 5%+ mispricings
- Logs opportunities found

### When Edge Detected:
```
🔍 EDGE FOUND: Trump wins NH primary
   Fair: 52% | Implied: 45% | Edge: 7%
   Side: YES
✅ ORDER FILLED: PRES-NH-TRUMP yes x15
```

### When Cutting Losers:
```
🔪 CUTTING LOSER: Biden wins general
   Edge flip: 6% (stop at 5%)
✅ Position closed | P&L: -$45.00
```

### Every 5 Minutes:
```
📊 PORTFOLIO SUMMARY
   Balance: $10,105.00
   Daily P&L: +$105.00 (+1.05%)
   Open Positions: 3
   Status: ACTIVE
```

---

## ⚠️ Safety Rules (READ THIS!)

### ✅ DO:
- [x] Start with `KALSHI_ENV=demo` (sandbox)
- [x] Test for weeks before live trading
- [x] Track Sharpe ratio, win rate, drawdown
- [x] Start small if going live ($100-500)
- [x] Monitor logs daily
- [x] Respect the 5% daily halt

### ❌ DON'T:
- [ ] Skip sandbox testing
- [ ] Trade more than you can afford to lose
- [ ] Override risk limits
- [ ] Ignore stop losses
- [ ] Use leverage (Kalshi doesn't offer it, but don't simulate it)
- [ ] Trade while drunk/emotional (let bot handle it!)

---

## 🐛 Troubleshooting

### "Authentication failed"
- Double-check API keys in `.env`
- Ensure no extra spaces/quotes
- Verify keys are for correct environment (demo vs prod)

### "No markets found"
- Check Kalshi API status: https://status.kalshi.com
- Verify network connection
- Try different market filters

### "Daily drawdown halt"
- This is working as intended! Capital preservation.
- Bot will resume next day
- Review what caused losses before continuing

### "Import errors"
- Ensure virtual environment is activated
- Reinstall: `pip install -r requirements.txt --force-reinstall`

---

## 📈 Next Steps After Testing

### Week 1-2: Observe
- Watch bot in sandbox
- Study which markets it trades
- Review fair value calculations
- Note edge detection accuracy

### Week 3-4: Optimize
- Tune `DEVIATION_THRESHOLD` (maybe 6-7% for higher quality)
- Adjust `RISK_PER_TRADE_PCT` based on results
- Add custom fair value sources
- Backtest on historical data

### Month 2+: Consider Live (If Profitable)
- Check metrics:
  - Sharpe Ratio >1.5 ✅
  - Win Rate >55% ✅
  - Max Drawdown <10% ✅
- Start with $100-500
- Scale 2x only after profitable quarter
- Keep 80%+ in sandbox for continued testing

---

## 📊 Recommended Metrics to Track

Create a spreadsheet with:
- **Daily P&L** ($)
- **Win Rate** (%)
- **Sharpe Ratio** (risk-adjusted returns)
- **Max Drawdown** (%)
- **Trades per Day** (#)
- **Average Edge** (% deviation)
- **Average Hold Time** (hours)

---

## 🎓 Learning Resources

### Watch Michael Beer's Demos:
- Study his execution speed (seconds, not minutes)
- Note his risk discipline (cuts losers immediately)
- Observe market selection (high-liquidity events)

### Read:
- Kalshi blog: Market mechanics
- Prediction market theory: Metaculus, Good Judgment Project
- Risk management: *The New Market Wizards* (Paul Tudor Jones)

### Practice:
- Paper trade for 100+ events
- Keep detailed trade journal
- Study winning vs losing trades
- Refine fair value models

---

## 💬 Support

**Issues?**
- Check logs: `kalshi_bot.log`
- Re-run `setup_check.py`
- Review `.env` configuration

**Questions?**
- Kalshi API Docs: https://kalshi.com/docs
- Michael Beer's X: https://x.com/michaelbeer01

---

**Remember: The bot's job is to grind edges, not hit home runs. Slow and steady wins the race.** 🐢💰

Good luck, and preserve that capital! 🛡️
