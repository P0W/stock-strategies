# Quick Start: Momentum Scoring v2

## TL;DR - What Changed?

**Old System Problems:**
- 5% weekly return → 1,167% annualized 🤯
- VWAP weighted twice (broken math)
- No normalization (weights don't work)

**New System Solutions:**
- ✅ Percentile ranking (0-100 scale)
- ✅ Simple weights (no double weighting)
- ✅ Strategy-aligned (3mo + 1mo periods)
- ✅ Risk filter (RSI overbought/oversold)

---

## The Formula (Simple!)

```python
# 1. Rank all 200 stocks on each metric (0-100 percentile)
rank_3mo_return = percentile(stock, "3mo_return")  # 0-100
rank_1mo_return = percentile(stock, "1mo_return")  # 0-100
rank_vwap = percentile(stock, "price_vs_vwap")     # 0-100

# 2. Weighted average
score = 0.5*rank_3mo + 0.3*rank_1mo + 0.2*rank_vwap  # 0-100

# 3. Penalize extremes
if RSI > 70 or RSI < 30:
    score = score * 0.5  # Cut in half
```

**That's it!** No complex annualization, no double weighting, no scale mismatches.

---

## Test It Now

```bash
# See the difference
python backend/compare_scoring_systems.py

# Test new scoring
python backend/momentum_score_v2.py
```

**Example Output:**
```
OLD SYSTEM: Score = 272.63 (dominated by 1-week spike of 1164%!)
NEW SYSTEM: Score = 81.0/100 (top 19% of stocks, balanced)
```

---

## Rebalancing Strategy

**Your Strategy:**
- **Weekly (Day 7+):** Rebalance if profit ≥ 2%
- **Quarterly (Day 90):** Mandatory rebalance

**Why v2 Works Better:**
- **3-month returns (50%)** = aligns with 90-day hold
- **1-month returns (30%)** = captures weekly profit moves
- **VWAP confirmation (20%)** = volume-backed moves only
- **RSI filter** = don't buy overbought stocks

---

## Integration Steps

### Step 1: Test with Existing Data (No API Changes)

```python
from backend.get_stocks import load_portfolio
from backend.momentum_score_v2 import adapt_legacy_data_format, calculate_all_momentum_scores_v2

# Load existing stock data
stocks = load_portfolio("stocks-nifty-200-2025-11-10.json")

# Adapt to new format (uses 1y as proxy for 3mo)
adapted = adapt_legacy_data_format(stocks)

# Calculate new scores
new_scores = calculate_all_momentum_scores_v2(adapted)

# See top 15
for i, stock in enumerate(new_scores[:15], 1):
    print(f"{i}. {stock['symbol']}: {stock['momentum_score']:.1f}/100")
```

### Step 2: Fetch Real 3-Month Data

Edit `backend/get_stocks.py`:

```python
# Line 249: Change duration list
for duration in ["3mo", "1mo"]:  # Was: ["1y", "1mo", "1w"]
    ...
```

### Step 3: Replace Scoring Function

```python
# In getStockList() after fetching all stocks:

# OLD:
# results = sorted(results, key=lambda x: x["composite_score"], reverse=True)

# NEW:
from momentum_score_v2 import calculate_all_momentum_scores_v2
results = calculate_all_momentum_scores_v2(results)
```

---

## Key Metrics to Monitor

After switching to v2, track:

1. **Turnover** - Should be lower (more stable rankings)
2. **Sharpe Ratio** - Risk-adjusted returns should improve
3. **Max Drawdown** - Better risk filtering with RSI
4. **Win Rate** - % of profitable rebalances

---

## What to Expect

### Better Stock Selection
- ❌ OLD: Stocks with 1-week spikes dominate
- ✅ NEW: Stocks with sustained 3-month + 1-month trends win

### Lower Turnover
- ❌ OLD: Weekly noise → constant rebalancing
- ✅ NEW: Quarterly alignment → stable positions

### Clearer Signals
- ❌ OLD: "This stock scored 272.63" (what does that mean?)
- ✅ NEW: "This stock is 81st percentile" (top 19%)

### Better Risk Management
- ❌ OLD: Might buy stocks at RSI 85 (overbought)
- ✅ NEW: RSI filter penalizes extremes

---

## Example: Full Workflow

**Friday, Nov 15, 2025 (7 days since last rebalance)**

```python
# 1. Check if should rebalance
portfolio_value = 512500
initial_investment = 500000
profit_pct = (512500 - 500000) / 500000 * 100  # 2.5%

if profit_pct >= 2.0:  # ✅ Yes, 2.5% >= 2%
    # 2. Fetch current rankings
    stocks = fetch_nifty_200_data()
    scored = calculate_all_momentum_scores_v2(stocks)

    # 3. Build new portfolio from top 15
    new_portfolio = build_portfolio(scored[:15], N=15, investment=512500)

    # 4. Execute rebalance
    rebalance_diff = calculate_rebalance(old_portfolio, new_portfolio)
    # Sells: INFY, ITC
    # Buys: BHARTI, TITAN
    # Holds: 11 others

    execute_trades(rebalance_diff)
```

---

## Files Reference

| File | Purpose |
|------|---------|
| `MOMENTUM_SCORE_ANALYSIS.md` | Detailed analysis of OLD system flaws |
| `MOMENTUM_SCORE_V2_DESIGN.md` | Complete NEW system documentation |
| `backend/momentum_score_v2.py` | Production-ready v2 implementation |
| `backend/compare_scoring_systems.py` | Side-by-side comparison tool |
| `QUICK_START_V2.md` | This file - quick reference |

---

## FAQ

**Q: Can I just drop this into production?**
A: Test first! Run backtest to compare old vs new on historical data.

**Q: What if I can't fetch 3-month data?**
A: Use `adapt_legacy_data_format()` to use 1-year data as proxy (not ideal but works for testing).

**Q: Do I need to change my rebalancing strategy?**
A: No! v2 is designed FOR your strategy (weekly 2% / quarterly 90-day).

**Q: What about transaction costs?**
A: Lower turnover + profit threshold means you rebalance less often, saving costs.

**Q: Can I customize weights?**
A: Yes! Edit line in `momentum_score_v2.py`:
```python
base_score = 0.5 * rank_3mo + 0.3 * rank_1mo + 0.2 * rank_vwap
# Change to whatever you want (should sum to 1.0)
```

---

## Next Steps

1. ✅ Run comparison: `python backend/compare_scoring_systems.py`
2. ⏳ Backtest on historical data
3. ⏳ Compare performance metrics
4. ⏳ Deploy to production if favorable

---

## Support

- Detailed docs: `MOMENTUM_SCORE_V2_DESIGN.md`
- Flaw analysis: `MOMENTUM_SCORE_ANALYSIS.md`
- Code: `backend/momentum_score_v2.py`

**Questions?** Check the detailed docs or review the comparison output.
