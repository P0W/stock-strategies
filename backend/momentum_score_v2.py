"""
Simplified Momentum Scoring System v2
Author: Claude Code Analysis

Design Philosophy:
- Percentile rank-based (0-100 scale)
- Aligned with weekly/quarterly rebalancing strategy
- Focus on relative strength, not absolute values
- Simple, interpretable, powerful
"""

import logging


def percentile_rank(values):
    """
    Convert a list of values to percentile ranks (0-100).

    Args:
        values: List of numeric values

    Returns:
        List of percentile ranks (0-100) corresponding to input values
    """
    if not values:
        return []

    n = len(values)
    # Create list of (value, original_index) pairs
    indexed_values = [(val, idx) for idx, val in enumerate(values)]
    # Sort by value
    sorted_values = sorted(indexed_values, key=lambda x: x[0])

    # Assign percentile ranks
    ranks = [0] * n
    for rank_position, (_, original_idx) in enumerate(sorted_values):
        # Convert position to percentile (0-100)
        percentile = (rank_position / (n - 1)) * 100 if n > 1 else 50
        ranks[original_idx] = percentile

    return ranks


def calculate_momentum_score_v2(stock_returns, current_price, rsi_value):
    """
    Calculate simplified momentum score for a single stock.

    Note: This is called per-stock, but needs all stocks' data for ranking.
    Use calculate_all_momentum_scores_v2() instead.

    Args:
        stock_returns: Dict with '3mo' and '1mo' return data
        current_price: Current stock price
        rsi_value: Recent RSI value (typically 1-month RSI)

    Returns:
        Dict with component values (to be ranked later)
    """
    # Extract raw metrics
    return_3mo = stock_returns.get("3mo", {}).get("return", 0)
    return_1mo = stock_returns.get("1mo", {}).get("return", 0)
    vwap_3mo = stock_returns.get("3mo", {}).get("vwap", current_price)

    # Calculate price premium over VWAP (percentage)
    price_vs_vwap = ((current_price - vwap_3mo) / vwap_3mo) * 100 if vwap_3mo > 0 else 0

    return {
        "return_3mo": return_3mo,
        "return_1mo": return_1mo,
        "price_vs_vwap": price_vs_vwap,
        "rsi": rsi_value,
    }


def calculate_all_momentum_scores_v2(stocks_data):
    """
    Calculate momentum scores for all stocks with proper percentile ranking.

    Args:
        stocks_data: List of dicts, each containing:
            - 'symbol': Stock symbol
            - 'returns': Dict with '3mo' and '1mo' data (each has 'return', 'vwap', 'rsi')
            - 'price': Current price

    Returns:
        List of dicts with original data plus 'momentum_score' and 'rank_details'
    """
    if not stocks_data:
        return []

    # Extract raw components for all stocks
    all_returns_3mo = []
    all_returns_1mo = []
    all_price_vs_vwap = []
    all_rsi = []

    for stock in stocks_data:
        # Use 1-month RSI as the primary RSI signal
        rsi_value = stock["returns"].get("1mo", {}).get("rsi", 50)

        components = calculate_momentum_score_v2(
            stock["returns"],
            stock["price"],
            rsi_value
        )

        all_returns_3mo.append(components["return_3mo"])
        all_returns_1mo.append(components["return_1mo"])
        all_price_vs_vwap.append(components["price_vs_vwap"])
        all_rsi.append(components["rsi"])

    # Convert to percentile ranks (0-100)
    rank_3mo = percentile_rank(all_returns_3mo)
    rank_1mo = percentile_rank(all_returns_1mo)
    rank_vwap = percentile_rank(all_price_vs_vwap)

    # Calculate momentum scores
    results = []
    for i, stock in enumerate(stocks_data):
        # Base score: weighted percentile ranks
        base_score = (
            0.50 * rank_3mo[i] +      # 50% - Quarterly trend
            0.30 * rank_1mo[i] +      # 30% - Recent momentum
            0.20 * rank_vwap[i]       # 20% - Volume confirmation
        )

        # RSI filter: penalize extremes (overbought/oversold)
        rsi = all_rsi[i]
        rsi_penalty = 1.0
        if rsi > 70:
            rsi_penalty = 0.5  # Overbought - reduce score by 50%
            rsi_status = "overbought"
        elif rsi < 30:
            rsi_penalty = 0.5  # Oversold - reduce score by 50%
            rsi_status = "oversold"
        else:
            rsi_status = "neutral"

        final_score = base_score * rsi_penalty

        # Add results
        result = stock.copy()
        result["momentum_score"] = final_score
        result["rank_details"] = {
            "rank_3mo_return": round(rank_3mo[i], 1),
            "rank_1mo_return": round(rank_1mo[i], 1),
            "rank_price_vs_vwap": round(rank_vwap[i], 1),
            "rsi_value": round(rsi, 1),
            "rsi_status": rsi_status,
            "rsi_penalty": rsi_penalty,
            "base_score": round(base_score, 2),
            "final_score": round(final_score, 2),
        }
        results.append(result)

    # Sort by momentum score (highest first)
    results.sort(key=lambda x: x["momentum_score"], reverse=True)

    return results


def adapt_legacy_data_format(legacy_stocks_data):
    """
    Adapt legacy data format (1y, 1mo, 1w) to new format (3mo, 1mo).

    Args:
        legacy_stocks_data: List of stocks with '1y', '1mo', '1w' returns

    Returns:
        List of stocks with '3mo', '1mo' returns for v2 scoring
    """
    adapted_data = []

    for stock in legacy_stocks_data:
        adapted_stock = stock.copy()

        # If we have 1-year data, use it as proxy for 3-month (not ideal, but works)
        # Better: fetch actual 3-month data from API
        if "returns" in stock:
            returns = stock["returns"]
            adapted_returns = {
                "3mo": returns.get("1y", {}),  # Use 1y as proxy (or fetch real 3mo)
                "1mo": returns.get("1mo", {}),
            }
            adapted_stock["returns"] = adapted_returns

        adapted_data.append(adapted_stock)

    return adapted_data


def display_momentum_rankings(stocks, top_n=15):
    """
    Display momentum rankings in a readable format.

    Args:
        stocks: List of stocks with momentum scores (from calculate_all_momentum_scores_v2)
        top_n: Number of top stocks to display
    """
    logging.info(f"\n{'='*100}")
    logging.info(f"TOP {top_n} MOMENTUM STOCKS")
    logging.info(f"{'='*100}")
    logging.info(
        f"{'Rank':<6} {'Symbol':<10} {'Score':<8} {'3Mo%':<8} {'1Mo%':<8} "
        f"{'VWAP%':<8} {'RSI':<6} {'Status':<12}"
    )
    logging.info(f"{'-'*100}")

    for rank, stock in enumerate(stocks[:top_n], 1):
        details = stock["rank_details"]
        logging.info(
            f"{rank:<6} {stock['symbol']:<10} {details['final_score']:<8.1f} "
            f"{details['rank_3mo_return']:<8.1f} {details['rank_1mo_return']:<8.1f} "
            f"{details['rank_price_vs_vwap']:<8.1f} {details['rsi_value']:<6.1f} "
            f"{details['rsi_status']:<12}"
        )

    logging.info(f"{'='*100}\n")


# Example usage for rebalancing strategy
def should_rebalance(portfolio_value, initial_investment, days_since_rebalance):
    """
    Determine if portfolio should be rebalanced based on your strategy.

    Strategy:
    - Weekly check: If profit >= 2%, rebalance
    - Else: Wait for quarterly (90 days), then mandatory rebalance

    Args:
        portfolio_value: Current portfolio value
        initial_investment: Initial investment amount
        days_since_rebalance: Days since last rebalance

    Returns:
        (should_rebalance: bool, reason: str)
    """
    profit_pct = ((portfolio_value - initial_investment) / initial_investment) * 100

    # Weekly check (every 7 days)
    if days_since_rebalance >= 7:
        if profit_pct >= 2.0:
            return True, f"Weekly profit trigger: {profit_pct:.2f}% >= 2%"

    # Quarterly mandatory rebalance
    if days_since_rebalance >= 90:
        return True, f"Quarterly mandatory rebalance: {days_since_rebalance} days"

    return False, f"Hold: {profit_pct:.2f}% profit, {days_since_rebalance} days since rebalance"


# Example test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Example data
    example_stocks = [
        {
            "symbol": "RELIANCE",
            "price": 2500,
            "returns": {
                "3mo": {"return": 15.5, "vwap": 2400, "rsi": 65},
                "1mo": {"return": 8.2, "vwap": 2450, "rsi": 68},
            }
        },
        {
            "symbol": "TCS",
            "price": 3500,
            "returns": {
                "3mo": {"return": 12.0, "vwap": 3400, "rsi": 55},
                "1mo": {"return": 5.5, "vwap": 3450, "rsi": 58},
            }
        },
        {
            "symbol": "INFY",
            "price": 1500,
            "returns": {
                "3mo": {"return": -2.0, "vwap": 1550, "rsi": 35},
                "1mo": {"return": 3.0, "vwap": 1480, "rsi": 45},
            }
        },
    ]

    # Calculate scores
    scored_stocks = calculate_all_momentum_scores_v2(example_stocks)

    # Display
    display_momentum_rankings(scored_stocks, top_n=3)

    # Test rebalancing logic
    print("\nRebalancing Strategy Tests:")
    print("-" * 60)

    test_cases = [
        (102000, 100000, 7, "Week 1, 2% profit"),
        (101500, 100000, 7, "Week 1, 1.5% profit"),
        (101000, 100000, 30, "1 month, 1% profit"),
        (105000, 100000, 90, "Quarter end, 5% profit"),
        (98000, 100000, 90, "Quarter end, -2% loss"),
    ]

    for portfolio_val, initial_inv, days, description in test_cases:
        should_reb, reason = should_rebalance(portfolio_val, initial_inv, days)
        print(f"{description:<30} → {should_reb:<5} | {reason}")
