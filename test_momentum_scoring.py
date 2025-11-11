"""
Test Momentum Scoring Methods on Real Historical Data

Compares 3 momentum scoring formulas:
1. LINEAR (your current backtest formula - what gave good results)
2. PRODUCTION (current get_stocks.py with compound annualization bug)
3. V2_PERCENTILE (proposed improvement)

Uses backtest/historical-prices.json (your real 3-year data)
"""

import json
import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')


def percentile_rank(values):
    """Convert values to percentile ranks (0-100)."""
    if not values:
        return []
    n = len(values)
    indexed = [(val, idx) for idx, val in enumerate(values)]
    sorted_vals = sorted(indexed, key=lambda x: x[0])
    ranks = [0] * n
    for rank_pos, (_, orig_idx) in enumerate(sorted_vals):
        percentile = (rank_pos / (n - 1)) * 100 if n > 1 else 50
        ranks[orig_idx] = percentile
    return ranks


def score_linear(stocks):
    """LINEAR: backtest.py:296 formula (what gave you good results)."""
    scored = []
    for symbol, data in stocks.items():
        if "1y" not in data["returns"]:
            continue
        try:
            score = (data["returns"]["1y"] +
                    data["returns"]["1mo"] * 12 +
                    data["returns"]["1w"] * 52)
            scored.append((symbol, score, data))
        except (KeyError, TypeError):
            continue
    return sorted(scored, key=lambda x: x[1], reverse=True)


def score_production(stocks):
    """PRODUCTION: get_stocks.py:128 with compound annualization."""
    scored = []
    for symbol, data in stocks.items():
        if "1y" not in data["returns"]:
            continue
        try:
            r1y = data["returns"]["1y"]
            r1mo = 100.0 * ((1 + data["returns"]["1mo"]) ** 12 - 1)
            r1w = 100.0 * ((1 + data["returns"]["1w"]) ** 52 - 1)

            # Time weights from get_stocks.py
            score = r1y * 0.2 + r1mo * 0.3 + r1w * 0.5
            scored.append((symbol, score, data))
        except (KeyError, TypeError, ZeroDivisionError):
            continue
    return sorted(scored, key=lambda x: x[1], reverse=True)


def score_v2(stocks):
    """V2: Percentile ranking (proposed improvement)."""
    symbols = []
    returns_1y = []
    returns_1mo = []
    stock_data = []

    for symbol, data in stocks.items():
        if "1y" not in data["returns"]:
            continue
        try:
            symbols.append(symbol)
            returns_1y.append(data["returns"]["1y"])
            returns_1mo.append(data["returns"]["1mo"])
            stock_data.append(data)
        except (KeyError, TypeError):
            continue

    rank_1y = percentile_rank(returns_1y)
    rank_1mo = percentile_rank(returns_1mo)

    scored = []
    for i, symbol in enumerate(symbols):
        score = 0.6 * rank_1y[i] + 0.4 * rank_1mo[i]
        scored.append((symbol, score, stock_data[i]))

    return sorted(scored, key=lambda x: x[1], reverse=True)


def calculate_portfolio_return(portfolio, current_prices):
    """Calculate return for a portfolio."""
    initial_value = sum(data["lp"] for _, _, data in portfolio)
    final_value = sum(current_prices.get(symbol, data["lp"]) for symbol, _, data in portfolio)

    if initial_value == 0:
        return 0
    return ((final_value - initial_value) / initial_value) * 100


def run_test(num_stocks=12, rebalance_days=90):
    """Run the scoring comparison test."""
    print("\n" + "="*80)
    print("MOMENTUM SCORING COMPARISON TEST")
    print("="*80)
    print(f"\nConfiguration:")
    print(f"  Portfolio size: {num_stocks} stocks")
    print(f"  Rebalance every: {rebalance_days} days")
    print(f"  Data source: backtest/historical-prices.json (3 years)")

    # Load historical data
    print(f"\n📂 Loading historical data...")
    with open("backtest/historical-prices.json", "r") as f:
        historical_data = json.load(f)

    dates = sorted(historical_data.keys())
    print(f"✅ Loaded {len(dates)} days ({dates[0]} to {dates[-1]})")

    # Find testable periods (where we have full data)
    test_periods = []
    for i in range(len(dates) - rebalance_days):
        start_date = dates[i]
        end_idx = min(i + rebalance_days, len(dates) - 1)
        end_date = dates[end_idx]

        # Check if start date has 1y data
        stocks_with_data = sum(1 for s in historical_data[start_date].values()
                              if "1y" in s.get("returns", {}))
        if stocks_with_data >= num_stocks:
            test_periods.append((start_date, end_date))

    print(f"📊 Found {len(test_periods)} testable {rebalance_days}-day periods")

    # Test every Nth period to avoid overlaps
    test_interval = rebalance_days // 7  # Test every week within rebalance period
    selected_periods = test_periods[::test_interval]

    print(f"🎯 Testing {len(selected_periods)} periods (sampling every {test_interval})")
    print("\n" + "-"*80)

    results = {
        "linear": [],
        "production": [],
        "v2": []
    }

    for idx, (start_date, end_date) in enumerate(selected_periods, 1):
        start_stocks = historical_data[start_date]
        end_prices = {symbol: data["lp"] for symbol, data in historical_data[end_date].items()}

        # Score with all 3 methods
        linear_scored = score_linear(start_stocks)[:num_stocks]
        prod_scored = score_production(start_stocks)[:num_stocks]
        v2_scored = score_v2(start_stocks)[:num_stocks]

        # Calculate returns
        linear_return = calculate_portfolio_return(linear_scored, end_prices)
        prod_return = calculate_portfolio_return(prod_scored, end_prices)
        v2_return = calculate_portfolio_return(v2_scored, end_prices)

        results["linear"].append(linear_return)
        results["production"].append(prod_return)
        results["v2"].append(v2_return)

        # Show progress every 10 periods
        if idx % 10 == 1 or idx == len(selected_periods):
            print(f"Period {idx}/{len(selected_periods)}: {start_date} → {end_date}")
            print(f"  Linear: {linear_return:+.2f}%  |  Production: {prod_return:+.2f}%  |  V2: {v2_return:+.2f}%")

    # Summary
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)

    for method, returns in results.items():
        avg = sum(returns) / len(returns)
        total = sum(returns)
        wins = sum(1 for r in returns if r > 0)
        win_rate = (wins / len(returns)) * 100
        best = max(returns)
        worst = min(returns)

        print(f"\n{method.upper()}:")
        print(f"  Average return/period:  {avg:+7.2f}%")
        print(f"  Total return:           {total:+7.2f}%")
        print(f"  Win rate:               {win_rate:7.1f}%  ({wins}/{len(returns)})")
        print(f"  Best period:            {best:+7.2f}%")
        print(f"  Worst period:           {worst:+7.2f}%")

    # Comparison
    print("\n" + "="*80)
    print("HEAD-TO-HEAD COMPARISON")
    print("="*80)

    linear_avg = sum(results["linear"]) / len(results["linear"])
    prod_avg = sum(results["production"]) / len(results["production"])
    v2_avg = sum(results["v2"]) / len(results["v2"])

    print(f"\n🏆 V2 vs LINEAR (your backtest formula):")
    diff = v2_avg - linear_avg
    if abs(diff) < 0.3:
        print(f"   ≈ TIE - Similar performance ({diff:+.2f}% difference)")
    elif diff > 0:
        print(f"   ✅ V2 WINS by {diff:+.2f}% per period")
        print(f"      Annualized: {diff * (365/rebalance_days):+.2f}%")
    else:
        print(f"   📉 LINEAR WINS by {abs(diff):+.2f}% per period")
        print(f"      Annualized: {abs(diff) * (365/rebalance_days):+.2f}%")

    print(f"\n🐛 PRODUCTION vs LINEAR:")
    diff = prod_avg - linear_avg
    if diff < -1.0:
        print(f"   ⚠️  PRODUCTION LOSES by {abs(diff):+.2f}% per period")
        print(f"      The compound annualization bug IS hurting performance!")
        print(f"      Annual cost: {abs(diff) * (365/rebalance_days):+.2f}%")
    else:
        print(f"   Difference: {diff:+.2f}%")

    # Win rate comparison
    linear_beats_v2 = sum(1 for i in range(len(results["linear"]))
                         if results["linear"][i] > results["v2"][i])
    v2_win_rate = ((len(results["linear"]) - linear_beats_v2) / len(results["linear"])) * 100

    print(f"\n📊 Direct matchups:")
    print(f"   V2 wins: {len(results['linear']) - linear_beats_v2} times ({v2_win_rate:.1f}%)")
    print(f"   LINEAR wins: {linear_beats_v2} times ({100-v2_win_rate:.1f}%)")

    print("\n" + "="*80)
    print("RECOMMENDATION")
    print("="*80)

    if v2_avg > linear_avg + 0.5:
        print("\n✅ Switch to V2 - Clear improvement over your current backtest formula")
    elif v2_avg > linear_avg - 0.3:
        print("\n✓ V2 is viable - Similar or better performance, with better properties:")
        print("  - No inflation bugs (1-week returns don't dominate)")
        print("  - Easier to interpret (percentile ranks)")
        print("  - More stable (less sensitive to outliers)")
    else:
        print("\n📊 Stick with LINEAR backtest formula for now")
        print("   But still fix the PRODUCTION bug (compound annualization)")

    print("\n")

    return results


if __name__ == "__main__":
    import sys

    # Parse command line arguments
    num_stocks = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    rebalance_days = int(sys.argv[2]) if len(sys.argv) > 2 else 90

    run_test(num_stocks=num_stocks, rebalance_days=rebalance_days)
