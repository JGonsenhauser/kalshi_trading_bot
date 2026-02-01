# 🤖 Kalshi Trading Bot - Michael Beer Style

**Automated prediction market trading bot mimicking [@michaelbeer01](https://x.com/michaelbeer01)'s disciplined approach: Fast execution, edge detection, and capital preservation.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 Philosophy: Cut the Noise, Preserve Capital, Ride the Edges

This bot embodies Michael Beer's approach from his [F1 trading bot demo](https://x.com/michaelbeer01) and [fast-trading threads](https://x.com/michaelbeer01):

✅ **No Hero Bets** - Pure math, not gambling  
✅ **Automate Fair Value** - Polls for politics, stats for sports, news for economics  
✅ **Trigger on Deviations** - 5-10% mispricings only  
✅ **Cut Losers Fast** - 5% edge flip = instant exit  
✅ **Let Winners Run** - Hold to settlement if probability holds  
✅ **1% Risk Cap** - Never more than 1% of capital per trade  
✅ **5% Daily Drawdown Halt** - Preserve capital when bleeding  

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10+
- Kalshi account ([sign up here](https://kalshi.com))
- NewsAPI key (optional, [get free key](https://newsapi.org))

### 2. Installation

```powershell
# Clone or navigate to project directory
cd "c:\Users\jgons\Agents\Kalshi Trading"

# Create virtual environment
python -m venv venv

# Activate venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```powershell
# Copy template and add your API keys
cp .env.example .env

# Edit .env with your keys
notepad .env
```

**Required settings in `.env`:**
```env
KALSHI_API_KEY=your_kalshi_api_key
KALSHI_API_SECRET=your_kalshi_secret
KALSHI_ENV=demo  # Start with 'demo' for sandbox!
NEWS_API_KEY=your_newsapi_key  # Optional
```

### 4. Run the Bot

```powershell
# Always start in SANDBOX mode for testing
python kalshi_bot.py
```

---

## 📁 Project Structure

```
Kalshi Trading/
├── kalshi_bot.py          # Main bot engine - event loop, API calls
├── config.py              # Centralized configuration management
├── risk_manager.py        # Position sizing, stops, drawdown limits
├── fair_value.py          # Fair value models (polls, news, arb)
├── requirements.txt       # Python dependencies
├── .env.example          # Config template
├── .env                  # Your secrets (gitignored)
├── .gitignore
└── README.md             # This file
```

---

## 🧠 How It Works

### Core Loop (Every 30 seconds):

1. **Scan Markets** - Fetch all open Kalshi markets via REST API
2. **Calculate Fair Value** - Compare to external data:
   - **Politics**: Aggregate polls from RCP/538
   - **Economics**: Parse news for CPI/jobs consensus
   - **Sports**: Historical stats (F1, NFL, etc.)
3. **Detect Edges** - Trigger if `|fair_value - implied_odds| > 5%`
4. **Execute** - Place market orders with 1% position sizing
5. **Monitor** - Cut positions if edge flips >5%, let winners run
6. **Halt** - Stop trading if daily drawdown >5%

### Fair Value Models

#### Politics (e.g., Elections)
```python
# Scrapes RealClearPolitics, 538 for polls
polls = [0.52, 0.48, 0.50]  # Recent poll results
fair_value = mean(polls)  # 0.50 (50%)
kalshi_price = 0.45  # Kalshi market at 45¢
edge = 0.50 - 0.45 = 5%  # BUY signal
```

#### Economics (e.g., CPI)
```python
# Fetches NewsAPI for "CPI forecast"
consensus = parse_news_sentiment()  # e.g., 0.60 (60% chance >3%)
kalshi_price = 0.50
edge = 0.60 - 0.50 = 10%  # BUY signal
```

#### Arbitrage Detection
```python
# Cross-market inconsistencies
market_a = "Trump wins primary" @ 0.70
market_b = "Trump wins general" @ 0.80  # Illogical
# If P(A) > P(B) but A implies B, arbitrage exists
```

### Risk Management (PTJ-Style)

| Rule | Implementation |
|------|---------------|
| **1% Max Risk** | `size = balance * 0.01 / entry_price` |
| **Cut Losers** | Exit if fair value shifts >5% against us |
| **Let Winners** | Hold to settlement if edge persists |
| **Daily Halt** | Stop if P&L <-5% from daily open |
| **Position Cap** | Max 5 simultaneous positions |

---

## ⚙️ Configuration Reference

Edit `.env` to customize:

```env
# Risk Settings (Conservative defaults)
RISK_PER_TRADE_PCT=0.01        # 1% per trade
MAX_DAILY_DRAWDOWN_PCT=0.05    # 5% daily loss limit
MAX_OPEN_POSITIONS=5           # Max concurrent trades

# Trading Parameters
DEVIATION_THRESHOLD=0.05       # 5% edge to trigger
STOP_LOSS_DEVIATION=0.05       # Cut if edge flips 5%
SCAN_INTERVAL_SECONDS=30       # Poll markets every 30s

# Environment
KALSHI_ENV=demo               # 'demo' or 'prod'
INITIAL_BALANCE=10000.0       # Starting capital
```

---

## 🛡️ Safety & Testing

### ⚠️ CRITICAL: Start in Sandbox

**NEVER run live without extensive sandbox testing!**

```powershell
# Set in .env
KALSHI_ENV=demo  # Uses Kalshi's demo API (paper trading)
```

Kalshi's demo environment:
- Free fake money
- Real market structure
- No financial risk
- Perfect for backtesting

### Recommended Testing Process

1. **Sandbox for 100+ Events** - Let bot trade demo markets for weeks
2. **Track Metrics**:
   - Sharpe Ratio >1.5
   - Max Drawdown <10%
   - Win Rate >55%
3. **Only Then** - Consider small live capital ($100-500)
4. **Scale Gradually** - Double capital only after profitable quarters

### Risk Warnings

⚠️ **Prediction markets are risky**  
⚠️ **No strategy is guaranteed**  
⚠️ **You can lose all capital**  
⚠️ **Regulations vary by jurisdiction**  
⚠️ **Check local laws before trading**  

This bot is for **educational purposes**. Use at your own risk.

---

## 📊 Monitoring & Logs

### Live Dashboard (console)
```
🚀 KALSHI BOT STARTING - Michael Beer Style
Environment: SANDBOX (Paper Trading)
Initial Balance: $10,000.00
Risk per Trade: 1.0%
Max Daily Drawdown: 5.0%
============================================================
🔍 EDGE FOUND: Trump wins NH primary | Fair: 52% | Implied: 45% | Edge: 7% | Side: YES
✅ ORDER FILLED: PRES-NH-TRUMP yes x15
📊 PORTFOLIO | Balance: $10,105.00 | Daily P&L: +$105.00 (+1.05%) | Positions: 3 | Status: ACTIVE
🔪 CUTTING LOSER: Biden wins general | Edge flip: 6% (stop at 5%)
```

### Log Files
- `kalshi_bot.log` - Full trade history, errors, debugging

---

## 🔧 Advanced Usage

### Customize Fair Value Models

Edit [fair_value.py](fair_value.py):

```python
async def _calculate_politics_fair_value(self, query: str, market: dict) -> float:
    # Add your own poll aggregation logic
    polls = await scrape_custom_source(query)
    weights = [0.5, 0.3, 0.2]  # Weight recent polls more
    fair_value = weighted_average(polls, weights)
    return fair_value
```

### Deploy on VPS (24/7 Trading)

```bash
# Example: AWS EC2 Ubuntu
sudo apt update
sudo apt install python3.10 python3.10-venv
git clone <your-repo>
cd Kalshi-Trading
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run in background with systemd or screen
screen -S kalshi
python kalshi_bot.py
# Ctrl+A, D to detach
```

### Backtest on Historical Data

```python
# TODO: Implement backtest.py
# Scrape historical Kalshi market data
# Replay events with bot logic
# Calculate returns, Sharpe, drawdown
```

---

## 🧪 Development Roadmap

- [x] Core API integration
- [x] Risk management system
- [x] Basic fair value models (politics, economics)
- [x] Arbitrage detection
- [ ] **Real poll scraping** (RCP, 538 via Selenium)
- [ ] **ML-based fair value** (XGBoost, LightGBM)
- [ ] **Backtesting framework** (historical Kalshi data)
- [ ] **WebSocket streaming** (sub-second latency)
- [ ] **Portfolio optimization** (Kelly Criterion sizing)
- [ ] **Multi-account support** (scale across accounts)

---

## 🤝 Contributing

Inspired by @michaelbeer01's work. Contributions welcome:

1. Fork the repo
2. Create feature branch (`git checkout -b feature/better-polls`)
3. Test extensively in sandbox
4. Submit PR with metrics (Sharpe, win rate, etc.)

---

## 📚 Resources

### Michael Beer's Demos
- [F1 Trading Bot Demo](https://x.com/michaelbeer01) - Live event trading
- [Fast-Trading Thread](https://x.com/michaelbeer01) - Speed execution

### Kalshi Documentation
- [API Docs](https://kalshi.com/docs) - REST endpoints
- [Market Rules](https://kalshi.com/rules) - Settlement logic
- [Sandbox Access](https://demo-api.kalshi.co) - Paper trading

### Data Sources
- [RealClearPolitics](https://www.realclearpolitics.com/epolls/) - Poll aggregation
- [FiveThirtyEight](https://projects.fivethirtyeight.com/polls/) - Election forecasts
- [NewsAPI](https://newsapi.org) - News feeds for economic data

### Prediction Market Theory
- *The Wisdom of Crowds* by James Surowiecki
- *Superforecasting* by Philip Tetlock
- [Metaculus](https://www.metaculus.com) - Forecasting community

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

**Disclaimer**: This software is for educational purposes only. Trading prediction markets involves substantial risk of loss. The authors assume no liability for financial losses incurred through use of this software.

---

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/kalshi-bot/issues)
- **Discussions**: Share strategies, results, improvements
- **Twitter**: Discuss with [@michaelbeer01](https://x.com/michaelbeer01) and the prediction market community

---

**Built with discipline. Trade with caution. Preserve capital first.** 🛡️
