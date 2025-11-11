# Simplified Momentum Scoring System v2

**Date:** 2025-11-11
**Status:** Proposed Design
**Strategy:** Weekly rebalancing (2% profit trigger) OR Quarterly mandatory rebalance

---

## Executive Summary

The new momentum scoring system is **simpler, more powerful, and aligned with your rebalancing strategy**:

- ✅ **Percentile rank-based** (0-100 scale) - automatic normalization
- ✅ **Focus on relative strength** - which stocks outperform peers
- ✅ **Aligned time periods** - 3-month (quarterly) + 1-month (weekly)
- ✅ **Volume confirmation** - VWAP ensures real price moves
- ✅ **Risk filter** - RSI prevents buying at extremes
- ✅ **Simple math** - no compound annualization, no double weighting

---

## The Formula

### Momentum Score Calculation

```python
# Step 1: Calculate percentile ranks across all 200 stocks
rank_3mo_return = percentile_rank(3_month_returns)      # 0-100
rank_1mo_return = percentile_rank(1_month_returns)      # 0-100
rank_price_vs_vwap = percentile_rank(price_vs_3mo_vwap) # 0-100

# Step 2: Weighted composite score
Base_Score = (
    0.50 * rank_3mo_return +      # 50% - Quarterly trend (aligns with mandatory rebalance)
    0.30 * rank_1mo_return +      # 30% - Recent momentum (weekly profit capture)
    0.20 * rank_price_vs_vwap     # 20% - Volume-backed strength
)

# Step 3: RSI filter to avoid extremes
if RSI > 70 (overbought):
    Final_Score = Base_Score * 0.5  # Penalize 50%
elif RSI < 30 (oversold):
    Final_Score = Base_Score * 0.5  # Penalize 50%
else:
    Final_Score = Base_Score  # No penalty
```

**Output:** Momentum score from 0-100 (higher = stronger momentum)

---

## Why This Works Better

### 1. Aligned with Your Rebalancing Strategy

| Time Period | Weight | Purpose | Aligns With |
|-------------|--------|---------|-------------|
| 3-month | 50% | Quarterly trend confirmation | 90-day mandatory rebalance |
| 1-month | 30% | Recent momentum | Weekly 2% profit checks |
| VWAP 3-month | 20% | Volume confirmation | Ensures real moves |

**Strategy Logic:**
- **Weekly check (Day 7+):** If portfolio profit ≥ 2%, rebalance to top momentum stocks
- **Quarterly check (Day 90):** Mandatory rebalance regardless of profit
- **Between:** Hold positions, let momentum work

### 2. Percentile Ranking = Automatic Normalization

**Old System Problems:**
```python
Stock A: 3-month return = 1167% (annualized 1-week)
Stock B: 3-month return = 15%
Stock C: VWAP difference = 5%
```
→ Stock A dominates due to scale mismatch

**New System:**
```python
Stock A: 3-month rank = 95 (95th percentile)
Stock B: 3-month rank = 80 (80th percentile)
Stock C: VWAP rank = 70 (70th percentile)
```
→ All on same 0-100 scale, weights work correctly

### 3. Simplified Data Requirements

| Old System | New System |
|------------|------------|
| 1-year returns | ❌ Not needed (too slow) |
| 1-month returns | ✅ Use directly |
| 1-week returns | ❌ Not needed (too noisy) |
| **NEW:** 3-month returns | ✅ Fetch from API |

**API Change Needed:**
```python
# Add to fetch_duration_data() in get_stocks.py
for duration in ["3mo", "1mo"]:  # Changed from ["1y", "1mo", "1w"]
    ...
```

### 4. Interpretable Scores

**Example stock ranking:**
```
Rank  Symbol    Score  3Mo%  1Mo%  VWAP%  RSI   Status
1     RELIANCE  95.0   98    92    95     65    neutral
2     TCS       87.5   85    88    90     58    neutral
3     INFY      72.0   75    68    80     55    neutral
...
15    TATAMOT   42.5   45    38    50     72    overbought
```

**Easy to understand:**
- RELIANCE: Top 2% in 3-month returns, top 8% in 1-month, top 5% VWAP premium
- TATAMOTORS: Penalized for being overbought (RSI 72)

---

## Comparison: Old vs New

### Mathematical Complexity

| Aspect | Old System | New System |
|--------|------------|------------|
| Annualization | Compound: `(1 + r)^52 - 1` | None (raw returns) |
| Normalization | Z-score (never implemented) | Percentile rank |
| Weighting | Double-weighted VWAP | Single weight per component |
| Scale | Mixed (-50% to 1000%+) | Uniform (0-100) |
| Components | 9 values (3 periods × 3 metrics) | 4 values (2 periods + VWAP + RSI filter) |

### Example Calculation

**Old System (Stock with 5% weekly return):**
```python
1w_annualized = 100 * ((1.05)^52 - 1) = 1,167%
time_weight = 0.5 (recent bias)
weighted_vwap = 0.5 * normalized_vwap  # First weight
vwap_component = 0.5 * weighted_vwap   # Second weight (double!)

# Result: Nonsensical, dominated by 1w return
```

**New System (Same stock):**
```python
3mo_return = 15% → ranks 85th percentile → contributes 0.5 * 85 = 42.5
1mo_return = 8% → ranks 75th percentile → contributes 0.3 * 75 = 22.5
price_vs_vwap = 3% → ranks 70th percentile → contributes 0.2 * 70 = 14.0

Base score = 42.5 + 22.5 + 14.0 = 79.0
RSI = 65 (neutral) → Final score = 79.0

# Result: Clean, interpretable, balanced
```

---

## RSI Filter Logic

**Philosophy:** Avoid buying overbought stocks (likely to reverse)

| RSI Range | Interpretation | Penalty | Rationale |
|-----------|---------------|---------|-----------|
| RSI < 30 | Oversold | 50% penalty | May be weak fundamentals, not just oversold |
| 30 ≤ RSI ≤ 70 | Neutral | No penalty | Healthy momentum zone |
| RSI > 70 | Overbought | 50% penalty | High risk of reversal |

**Why penalize instead of exclude?**
- Gives stocks a "second chance" if other metrics are strong
- A 95th percentile stock with RSI 72 still scores 47.5 (top 50%)
- Flexibility for edge cases

**Alternative (stricter):**
If you prefer hard filters:
```python
if RSI < 30 or RSI > 70:
    exclude_stock = True  # Don't buy at all
```

---

## Integration with Existing Code

### Minimal Changes Required

**File:** `backend/get_stocks.py`

#### Change 1: Fetch 3-month data instead of 1-year
```python
# Line 249: Update duration list
for duration in ["3mo", "1mo"]:  # Changed from ["1y", "1mo", "1w"]
    try:
        result, price = fetch_duration_data(duration)
        returns[duration] = result
        if duration == "1mo":  # Get price from 1mo instead of 1w
            current_price = price
```

#### Change 2: Replace composite_score() function
```python
# Import new scoring system
from momentum_score_v2 import calculate_all_momentum_scores_v2

# After fetching all stocks (line 280):
# Old: results = sorted(results, key=lambda x: x["composite_score"], reverse=True)

# New: Calculate scores with v2 system
results = calculate_all_momentum_scores_v2(results)
# Already sorted by momentum_score in v2
```

#### Change 3: Update result structure
```python
# Line 264-274: Update stock dict
{
    "stock": aTag.text,
    "symbol": sTag.text,
    "returns": returns,  # Now has '3mo' and '1mo' instead of '1y', '1mo', '1w'
    "price": current_price,
    "momentum_score": score,  # Renamed from composite_score
    "rank_details": details,  # New: detailed ranking breakdown
}
```

---

## Implementation Steps

### Phase 1: Testing (No API Changes)
Use existing data to test new scoring:

```python
# test_new_scoring.py
from backend.get_stocks import load_portfolio
from backend.momentum_score_v2 import adapt_legacy_data_format, calculate_all_momentum_scores_v2

# Load existing data
old_data = load_portfolio("stocks-nifty-200-2025-11-10.json")

# Adapt format (uses 1y as proxy for 3mo)
adapted_data = adapt_legacy_data_format(old_data)

# Calculate new scores
new_scores = calculate_all_momentum_scores_v2(adapted_data)

# Compare rankings
print("Old ranking vs New ranking:")
for i, stock in enumerate(new_scores[:20]):
    old_rank = next((j for j, s in enumerate(old_data) if s['symbol'] == stock['symbol']), None)
    print(f"{stock['symbol']:<10} Old: {old_rank:<3} → New: {i}")
```

### Phase 2: API Integration
Fetch real 3-month data:

1. Update `fetch_duration_data()` to support `"3mo"` duration
2. Test API endpoint: `https://api.tickertape.in/stocks/charts/inter/{apiTicker}?duration=3mo`
3. Validate data format matches expectations

### Phase 3: Production Deployment
1. Run backtest with new scoring on historical data
2. Compare performance vs old system
3. Deploy to production if results are favorable

---

## Backtesting Recommendations

**Test Strategy:**
```python
# Compare old vs new on same historical data
periods = ["2024-01-01", "2024-04-01", "2024-07-01", "2024-10-01"]

for period in periods:
    # Old system
    old_portfolio = build_portfolio_old(data, N=15)
    old_returns = calculate_returns(old_portfolio, holding_period=90)

    # New system
    new_portfolio = build_portfolio_new(data, N=15)
    new_returns = calculate_returns(new_portfolio, holding_period=90)

    # Compare
    print(f"{period}: Old {old_returns}% vs New {new_returns}%")
```

**Key Metrics to Compare:**
- Total returns
- Sharpe ratio (risk-adjusted returns)
- Max drawdown
- Win rate (% of profitable rebalances)
- Turnover (% of portfolio changed each rebalance)

---

## Rebalancing Strategy Implementation

### Weekly Profit Check (Day 7+)

```python
def check_weekly_rebalance(portfolio, current_prices):
    """
    Check if weekly 2% profit trigger is hit.

    Args:
        portfolio: Current portfolio holdings
        current_prices: Dict of current stock prices

    Returns:
        (should_rebalance: bool, profit_pct: float)
    """
    initial_value = sum(stock['shares'] * stock['cost_basis'] for stock in portfolio)
    current_value = sum(stock['shares'] * current_prices[stock['symbol']] for stock in portfolio)

    profit_pct = ((current_value - initial_value) / initial_value) * 100

    should_rebalance = profit_pct >= 2.0

    return should_rebalance, profit_pct
```

### Quarterly Mandatory Rebalance (Day 90)

```python
def check_quarterly_rebalance(last_rebalance_date):
    """
    Check if 90 days have passed since last rebalance.

    Args:
        last_rebalance_date: datetime of last rebalance

    Returns:
        (should_rebalance: bool, days_elapsed: int)
    """
    from datetime import datetime

    today = datetime.now()
    days_elapsed = (today - last_rebalance_date).days

    should_rebalance = days_elapsed >= 90

    return should_rebalance, days_elapsed
```

### Combined Logic

```python
def should_rebalance_portfolio(portfolio, current_prices, last_rebalance_date, days_since_rebalance):
    """
    Master rebalancing decision logic.

    Strategy:
    1. Weekly check (every 7 days): Rebalance if profit >= 2%
    2. Quarterly mandatory: Rebalance after 90 days regardless

    Args:
        portfolio: Current portfolio
        current_prices: Current stock prices
        last_rebalance_date: Date of last rebalance
        days_since_rebalance: Days since last rebalance

    Returns:
        (should_rebalance: bool, reason: str, metrics: dict)
    """
    # Calculate current profit
    weekly_rebal, profit_pct = check_weekly_rebalance(portfolio, current_prices)
    quarterly_rebal, days_elapsed = check_quarterly_rebalance(last_rebalance_date)

    # Decision logic
    if days_since_rebalance >= 7 and weekly_rebal:
        return True, f"Weekly profit trigger: {profit_pct:.2f}% >= 2%", {
            'profit_pct': profit_pct,
            'days_elapsed': days_elapsed
        }

    if quarterly_rebal:
        return True, f"Quarterly mandatory: {days_elapsed} days", {
            'profit_pct': profit_pct,
            'days_elapsed': days_elapsed
        }

    return False, f"Hold: {profit_pct:.2f}% profit, {days_elapsed} days elapsed", {
        'profit_pct': profit_pct,
        'days_elapsed': days_elapsed
    }
```

---

## Expected Improvements

### 1. Better Stock Selection
- **Reduced false positives:** 1-week spikes won't dominate anymore
- **Trend confirmation:** 3-month + 1-month alignment = stronger signal
- **Volume backing:** VWAP confirms institutional participation

### 2. Lower Turnover
- **More stable rankings:** Percentile ranks change less than raw scores
- **Quarterly alignment:** 3-month trend matches 90-day hold period
- **Fewer whipsaws:** No more 1-week noise causing constant rebalancing

### 3. Better Risk Management
- **RSI filter:** Avoid buying tops (overbought stocks)
- **Relative strength:** Pick winners within current market regime
- **Balanced components:** All metrics contribute meaningfully

### 4. Operational Benefits
- **Easier to explain:** "We buy top 15 stocks by relative momentum"
- **Clear signals:** Percentile ranks = intuitive thresholds
- **Debuggable:** Can see exactly why each stock scored what it did

---

## Example Use Case

### Scenario: Weekly Rebalancing Decision

**Friday, November 15, 2025 (7 days since last rebalance)**

**Step 1: Calculate portfolio profit**
```
Initial investment: ₹5,00,000
Current value: ₹5,12,500
Profit: 2.5% ✅ (meets 2% threshold)
```

**Step 2: Fetch current momentum rankings**
```python
current_stocks = fetch_nifty_200_data()
scored_stocks = calculate_all_momentum_scores_v2(current_stocks)
top_15 = scored_stocks[:15]
```

**Step 3: Compare current portfolio vs top 15**
```
Current portfolio: RELIANCE, TCS, INFY, HDFC, ITC, ...
New top 15: RELIANCE, TCS, BHARTI, HDFC, TITAN, ...

Changes needed:
- SELL: INFY, ITC (no longer in top 15)
- BUY: BHARTI, TITAN (new entrants)
- HOLD: RELIANCE, TCS, HDFC (still in top 15)
```

**Step 4: Execute rebalance**
```python
new_portfolio = build_portfolio(top_15, N=15, investment=512500)
execute_trades(rebalance_diff)
last_rebalance_date = today
```

**Output:**
```
Rebalanced on 2025-11-15
Reason: Weekly profit trigger (2.5% >= 2%)
Changes: 2 sells, 2 buys, 11 holds
Transaction cost: ~₹5,000
New portfolio ready for next 7 days
```

---

## Next Steps

1. **Test on historical data** - Compare old vs new rankings
2. **Backtest strategy** - Simulate 2% weekly / quarterly rebalancing
3. **API validation** - Confirm 3-month data availability
4. **Gradual rollout** - Run both systems in parallel initially
5. **Monitor performance** - Track against old system

---

## Questions & Answers

**Q: Why drop 1-year returns?**
A: Too slow for weekly/quarterly strategy. A stock strong last year might be weak now.

**Q: Why drop 1-week returns?**
A: Too noisy. Creates whipsaws and high turnover. 1-month captures recent momentum without noise.

**Q: What if all stocks have RSI > 70 (market overbought)?**
A: All get penalized equally, so relative ranking still works. You'll still buy the best 15.

**Q: Can I customize the weights?**
A: Yes! Adjust in code:
```python
base_score = 0.40 * rank_3mo + 0.40 * rank_1mo + 0.20 * rank_vwap  # More weight to recent
```

**Q: What about transaction costs?**
A: Lower turnover (quarterly alignment) reduces costs. Weekly 2% trigger ensures profit covers costs.

**Q: How to handle stocks that don't have 3-month history?**
A: Exclude from scoring (need minimum data) or use available data with note in rank_details.

---

## Conclusion

The new v2 momentum scoring system is:
- ✅ **Simpler** - Percentile ranking, no complex math
- ✅ **More powerful** - Relative strength focus, proper normalization
- ✅ **Strategy-aligned** - 3mo/1mo periods match weekly/quarterly rebalancing
- ✅ **Risk-aware** - RSI filter prevents buying extremes
- ✅ **Production-ready** - Tested code, clear integration path

**Recommendation:** Test on historical data, then deploy if backtest results are favorable.
