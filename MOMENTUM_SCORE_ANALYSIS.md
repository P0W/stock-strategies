# Momentum Score Calculation - Flaw Analysis

**Date:** 2025-11-11
**Analyzed File:** `backend/get_stocks.py`
**Function:** `composite_score()` (lines 120-155)

## Executive Summary

The momentum scoring system contains **5 critical flaws** that significantly distort stock rankings:

1. **Unrealistic annualization** of short-term returns (inflates values by 100-1000x)
2. **Double weighting** of VWAP component
3. **Missing z-score normalization** across stocks (contradicts README documentation)
4. **Inconsistent component weighting**
5. **Raw RSI values** without peer normalization

These flaws cause the scoring system to produce incorrect rankings, particularly favoring stocks with short-term volatility spikes.

---

## Detailed Analysis

### FLAW #1: Unrealistic Annualization of Short-Term Returns
**Severity:** CRITICAL
**Location:** `backend/get_stocks.py:127-129`

#### Current Code:
```python
normalized_returns = [
    returns["1y"]["return"],  # Already annualized
    100.0 * ((1 + returns["1mo"]["return"] / 100.0) ** 12 - 1),  # Compounds 12x
    100.0 * ((1 + returns["1w"]["return"] / 100.0) ** 52 - 1),   # Compounds 52x
]
```

#### Problem:
The code uses **compound annualization** which assumes short-term returns will compound at the same rate for an entire year. This creates unrealistic values:

| Original Return | Period | Annualized Value | Realistic? |
|----------------|--------|------------------|------------|
| 5% | 1 week | 1,167% | ❌ No |
| 10% | 1 month | 214% | ❌ No |
| 20% | 1 year | 20% | ✅ Yes |

#### Impact:
- Stocks with short-term price spikes get massively inflated scores
- Recent returns (1w) dominate the entire calculation due to 52x compounding
- Time weighting becomes meaningless when values differ by 50-100x

#### Recommended Fix:
Use simple linear scaling instead of compounding:

```python
# Option 1: Simple linear annualization
normalized_returns = [
    returns["1y"]["return"],
    returns["1mo"]["return"] * 12,  # Linear scaling
    returns["1w"]["return"] * 52,   # Linear scaling
]

# Option 2: Use raw returns without annualization
normalized_returns = [
    returns["1y"]["return"],
    returns["1mo"]["return"],
    returns["1w"]["return"],
]
```

---

### FLAW #2: Double Weighting of VWAP Component
**Severity:** CRITICAL
**Location:** `backend/get_stocks.py:132-146`

#### Current Code:
```python
weighted_vwap = [0.2, 0.3, 0.5]  # First set of weights
normalized_vwap = [
    (price - returns["1y"]["vwap"]) * weighted_vwap[0] / price,   # Weight applied
    (price - returns["1mo"]["vwap"]) * weighted_vwap[1] / price,  # Weight applied
    (price - returns["1w"]["vwap"]) * weighted_vwap[2] / price,   # Weight applied
]

time_weights = [0.2, 0.3, 0.5]  # Second set of weights (same values!)
vwap_component = sum(v * w for v, w in zip(normalized_vwap, time_weights))  # Weight applied AGAIN
```

#### Problem:
VWAP values are weighted twice, creating incorrect effective weights:

| Period | First Weight | Second Weight | Effective Weight | Expected Weight |
|--------|-------------|---------------|------------------|-----------------|
| 1y | 0.2 | 0.2 | 0.04 (0.2 × 0.2) | 0.2 |
| 1mo | 0.3 | 0.3 | 0.09 (0.3 × 0.3) | 0.3 |
| 1w | 0.5 | 0.5 | 0.25 (0.5 × 0.5) | 0.5 |
| **Total** | - | - | **0.38** | **1.0** |

The effective weights don't sum to 1.0, and the distribution is quadratic instead of linear.

#### Impact:
- VWAP component receives inconsistent weighting compared to returns and RSI
- Recent VWAP (1w) gets less weight than intended (0.25 effective vs 0.5 expected)
- Component contributions become mathematically incorrect

#### Recommended Fix:
Remove the first weighting step:

```python
# Remove weighted_vwap variable entirely
normalized_vwap = [
    (price - returns["1y"]["vwap"]) / price,
    (price - returns["1mo"]["vwap"]) / price,
    (price - returns["1w"]["vwap"]) / price,
]

# Apply time_weights only once
time_weights = [0.2, 0.3, 0.5]
vwap_component = sum(v * w for v, w in zip(normalized_vwap, time_weights))
```

---

### FLAW #3: Missing Z-Score Normalization
**Severity:** HIGH
**Location:** `backend/get_stocks.py:120-155`

#### Current Code:
```python
def z_score_normalize(data):
    # Function exists but is NEVER called!
    ...

def composite_score(returns, price):
    # No cross-stock normalization happens
    returns_component = sum(r * w for r, w in zip(normalized_returns, time_weights))
    vwap_component = sum(v * w for v, w in zip(normalized_vwap, time_weights))
    rsi_component = sum(r * w for r, w in zip(normalized_rsi, time_weights))

    composite_score_result = (
        weight_returns * returns_component
        + weight_vwap * vwap_component
        + weight_rsi * rsi_component
    )
```

#### Problem:
The README states:
> "To ensure that all metrics are on a consistent scale, they are normalized. This process scales the values so that they have similar ranges, making them directly comparable."

However, **no cross-stock normalization occurs**. Each component operates on different scales:

| Component | Typical Range | Example Values |
|-----------|---------------|----------------|
| Returns | -50% to +1000% (due to Flaw #1) | -20, 50, 500, 1200 |
| VWAP | -10% to +10% | -0.05, 0.02, 0.08 |
| RSI | 0 to 100 | 35, 65, 72 |

#### Impact:
- The component with largest absolute values dominates the score
- Due to Flaw #1, annualized returns reach 1000%, overwhelming VWAP and RSI
- Declared weights (40%, 30%, 30%) become meaningless
- Example: A return of 1000% with 40% weight = 400, while RSI of 70 with 30% weight = 21

#### Recommended Fix:
Implement two-pass calculation with z-score normalization:

```python
def calculate_all_composite_scores(all_stocks_data):
    """Calculate composite scores with proper cross-stock normalization."""

    # First pass: Calculate raw components for all stocks
    all_returns_components = []
    all_vwap_components = []
    all_rsi_components = []

    for stock_data in all_stocks_data:
        returns, price = stock_data['returns'], stock_data['price']

        # Calculate raw components (fixed from Flaws #1 and #2)
        returns_vals = [
            returns["1y"]["return"],
            returns["1mo"]["return"] * 12,  # Linear scaling
            returns["1w"]["return"] * 52,
        ]
        vwap_vals = [
            (price - returns["1y"]["vwap"]) / price,
            (price - returns["1mo"]["vwap"]) / price,
            (price - returns["1w"]["vwap"]) / price,
        ]
        rsi_vals = [
            returns["1y"]["rsi"],
            returns["1mo"]["rsi"],
            returns["1w"]["rsi"],
        ]

        time_weights = [0.2, 0.3, 0.5]
        returns_comp = sum(r * w for r, w in zip(returns_vals, time_weights))
        vwap_comp = sum(v * w for v, w in zip(vwap_vals, time_weights))
        rsi_comp = sum(r * w for r, w in zip(rsi_vals, time_weights))

        all_returns_components.append(returns_comp)
        all_vwap_components.append(vwap_comp)
        all_rsi_components.append(rsi_comp)

    # Second pass: Z-score normalize across all stocks
    normalized_returns = z_score_normalize(all_returns_components)
    normalized_vwap = z_score_normalize(all_vwap_components)
    normalized_rsi = z_score_normalize(all_rsi_components)

    # Third pass: Calculate final composite scores
    weight_returns = 0.4
    weight_vwap = 0.3
    weight_rsi = 0.3

    final_scores = []
    for i in range(len(all_stocks_data)):
        score = (
            weight_returns * normalized_returns[i] +
            weight_vwap * normalized_vwap[i] +
            weight_rsi * normalized_rsi[i]
        )
        final_scores.append(score)

    return final_scores
```

---

### FLAW #4: Inconsistent Component Weighting
**Severity:** MEDIUM
**Location:** `backend/get_stocks.py:142-146`

#### Current Code:
```python
time_weights = [0.2, 0.3, 0.5]

returns_component = sum(r * w for r, w in zip(normalized_returns, time_weights))  # ✓
vwap_component = sum(v * w for v, w in zip(normalized_vwap, time_weights))        # ✗ Double weighted
rsi_component = sum(r * w for r, w in zip(normalized_rsi, time_weights))          # ✓
```

#### Problem:
Only VWAP is double-weighted (due to Flaw #2), creating inconsistency.

#### Impact:
VWAP is effectively penalized compared to returns and RSI, making the declared component weights (40%, 30%, 30%) inaccurate.

#### Recommended Fix:
Addressed by fixing Flaw #2.

---

### FLAW #5: Raw RSI Values Without Peer Normalization
**Severity:** MEDIUM
**Location:** `backend/get_stocks.py:139`

#### Current Code:
```python
normalized_rsi = [returns["1y"]["rsi"], returns["1mo"]["rsi"], returns["1w"]["rsi"]]
```

#### Problem:
RSI values (0-100) are used as absolute numbers without normalization relative to other stocks.

- An RSI of 70 might be average for the current market
- Or it might indicate overbought conditions
- Without peer comparison, we can't tell

#### Impact:
Stocks with high RSI are favored regardless of whether that RSI is high relative to peers or just absolute value.

#### Recommended Fix:
Addressed by fixing Flaw #3 (cross-stock z-score normalization).

---

## Code Quality Issues

### Unused Function
The `z_score_normalize()` function is defined but never used, suggesting the normalization was planned but not implemented.

### Misleading Documentation
The README claims normalization occurs, but the code doesn't implement it.

---

## Testing Recommendations

To verify these flaws, test with example data:

```python
# Example stock with 5% weekly return
stock_A = {
    "1y": {"return": 20, "vwap": 100, "rsi": 60},
    "1mo": {"return": 3, "vwap": 105, "rsi": 65},
    "1w": {"return": 5, "vwap": 108, "rsi": 70}
}
price_A = 110

# Expected annualized 1w return: ~260% (simple) or ~1167% (compound - current bug)
# Expected behavior: Should not dominate 1y return of 20%
```

---

## Priority Recommendations

1. **CRITICAL - Immediate Fix:** Flaw #1 (Annualization)
   - Causes 100-1000x inflation of short-term returns
   - Single week can completely dominate score

2. **CRITICAL - Immediate Fix:** Flaw #2 (Double Weighting)
   - Breaks stated weight distribution
   - Easy to fix (remove one line)

3. **HIGH - Important Fix:** Flaw #3 (Z-Score Normalization)
   - Required to make component weights meaningful
   - Aligns code with documentation
   - More complex refactoring needed

4. **MEDIUM - Cleanup:** Flaws #4 & #5
   - Addressed by fixes above
   - Improve consistency

---

## Conclusion

The current momentum scoring system has fundamental mathematical flaws that produce incorrect stock rankings. The combination of:

- Extreme annualization (1000%+ values)
- Double weighting of one component
- No cross-stock normalization

...means that stocks with short-term volatility spikes are massively over-ranked, and the stated importance of different metrics (40/30/30) is not actually reflected in the calculations.

**Recommendation:** Implement all fixes before using this system for real investment decisions.
