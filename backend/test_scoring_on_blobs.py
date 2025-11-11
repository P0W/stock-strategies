"""
Test different momentum scoring methods on historical Azure Blob data.

This script:
1. Lists all available nifty200-symbols blob files
2. For weekly/monthly intervals, applies different scoring formulas
3. Compares which stocks would be selected
4. Calculates actual returns for each method
"""

import datetime
import json
import logging
from BlobService import BlobService
import get_stocks as strategy

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def percentile_rank(values):
    """Convert list of values to percentile ranks (0-100)."""
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


def score_current_production(stocks):
    """Current production scoring (with compound annualization bug)."""
    scored = []
    for stock in stocks:
        try:
            r1y = stock["returns"]["1y"]["return"]
            r1mo = 100.0 * ((1 + stock["returns"]["1mo"]["return"] / 100.0) ** 12 - 1)
            r1w = 100.0 * ((1 + stock["returns"]["1w"]["return"] / 100.0) ** 52 - 1)

            time_weights = [0.2, 0.3, 0.5]
            returns_component = r1y * time_weights[0] + r1mo * time_weights[1] + r1w * time_weights[2]

            # Simplified (just using returns, similar to composite_score)
            score = 0.4 * returns_component

            scored.append({
                "symbol": stock["symbol"],
                "score": score,
                "stock": stock
            })
        except (KeyError, TypeError, ZeroDivisionError):
            continue

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


def score_linear_backtest(stocks):
    """Linear backtest scoring (what gave you good results)."""
    scored = []
    for stock in stocks:
        try:
            r1y = stock["returns"]["1y"]["return"]
            r1mo = stock["returns"]["1mo"]["return"]
            r1w = stock["returns"]["1w"]["return"]

            # Linear scaling (backtest formula)
            score = r1y + r1mo * 12 + r1w * 52

            scored.append({
                "symbol": stock["symbol"],
                "score": score,
                "stock": stock
            })
        except (KeyError, TypeError):
            continue

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


def score_v2_percentile(stocks):
    """V2 percentile ranking scoring."""
    # Extract returns
    returns_1y = []
    returns_1mo = []
    valid_stocks = []

    for stock in stocks:
        try:
            returns_1y.append(stock["returns"]["1y"]["return"])
            returns_1mo.append(stock["returns"]["1mo"]["return"])
            valid_stocks.append(stock)
        except (KeyError, TypeError):
            continue

    # Calculate percentile ranks
    rank_1y = percentile_rank(returns_1y)
    rank_1mo = percentile_rank(returns_1mo)

    # Calculate scores
    scored = []
    for i, stock in enumerate(valid_stocks):
        score = 0.6 * rank_1y[i] + 0.4 * rank_1mo[i]
        scored.append({
            "symbol": stock["symbol"],
            "score": score,
            "stock": stock
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


def calculate_portfolio_return(portfolio, future_prices):
    """Calculate return for a portfolio given future prices."""
    initial_value = sum(stock["stock"]["price"] * stock["stock"].get("weight", 1) for stock in portfolio)

    future_value = 0
    for stock in portfolio:
        symbol = stock["symbol"]
        if symbol in future_prices:
            future_value += future_prices[symbol] * stock["stock"].get("weight", 1)

    if initial_value == 0:
        return 0

    return ((future_value - initial_value) / initial_value) * 100


def get_available_dates(blob_service, lookback_days=365):
    """Get all available nifty200-symbols blob dates."""
    blob_names = blob_service.list_blobs(file_prefix="all_symbols/nifty200-symbols-")

    dates = []
    for blob_name in blob_names:
        # Extract date from: all_symbols/nifty200-symbols-2024-01-15.json
        try:
            date_str = blob_name.split("nifty200-symbols-")[1].replace(".json", "")
            date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")

            # Filter to lookback period
            cutoff = datetime.datetime.now() - datetime.timedelta(days=lookback_days)
            if date_obj >= cutoff:
                dates.append(date_str)
        except (IndexError, ValueError):
            continue

    return sorted(dates)


def test_scoring_methods(account_name="stockstrategies", lookback_days=180, num_stocks=12, rebalance_days=90):
    """Test all scoring methods on historical data."""
    print("\n" + "="*80)
    print(f"TESTING SCORING METHODS ON AZURE BLOB DATA")
    print("="*80)
    print(f"\nParameters:")
    print(f"  - Lookback: {lookback_days} days")
    print(f"  - Number of stocks: {num_stocks}")
    print(f"  - Rebalance frequency: {rebalance_days} days")
    print(f"  - Azure account: {account_name}")

    blob_service = BlobService(account_name)

    # Get available dates
    print(f"\n📅 Finding available historical data...")
    available_dates = get_available_dates(blob_service, lookback_days)

    if not available_dates:
        print("❌ No historical data found in blob storage!")
        return

    print(f"✅ Found {len(available_dates)} days of data")
    print(f"   Date range: {available_dates[0]} to {available_dates[-1]}")

    # Select rebalance dates (every N days)
    rebalance_dates = []
    for i in range(0, len(available_dates), rebalance_days):
        if i + rebalance_days < len(available_dates):  # Ensure we have future data
            rebalance_dates.append((available_dates[i], available_dates[i + rebalance_days]))

    print(f"\n📊 Testing on {len(rebalance_dates)} rebalancing periods")
    print("-"*80)

    # Track results
    results = {
        "production": {"returns": [], "portfolios": []},
        "linear": {"returns": [], "portfolios": []},
        "v2": {"returns": [], "portfolios": []}
    }

    for start_date, end_date in rebalance_dates:
        print(f"\n🔄 Period: {start_date} → {end_date}")

        # Fetch start date data
        start_blob = f"all_symbols/nifty200-symbols-{start_date}.json"
        start_data = blob_service.get_blob_data_if_exists(start_blob)

        # Fetch end date data (for prices)
        end_blob = f"all_symbols/nifty200-symbols-{end_date}.json"
        end_data = blob_service.get_blob_data_if_exists(end_blob)

        if not start_data or not end_data:
            print(f"  ⚠️  Missing data, skipping...")
            continue

        # Get future prices
        future_prices = {stock["symbol"]: stock["price"] for stock in end_data}

        # Score with all 3 methods
        try:
            prod_scored = score_current_production(start_data)
            linear_scored = score_linear_backtest(start_data)
            v2_scored = score_v2_percentile(start_data)

            # Get top N from each
            prod_top = prod_scored[:num_stocks]
            linear_top = linear_scored[:num_stocks]
            v2_top = v2_scored[:num_stocks]

            # Calculate returns
            prod_return = calculate_portfolio_return(prod_top, future_prices)
            linear_return = calculate_portfolio_return(linear_top, future_prices)
            v2_return = calculate_portfolio_return(v2_top, future_prices)

            results["production"]["returns"].append(prod_return)
            results["linear"]["returns"].append(linear_return)
            results["v2"]["returns"].append(v2_return)

            results["production"]["portfolios"].append([s["symbol"] for s in prod_top])
            results["linear"]["portfolios"].append([s["symbol"] for s in linear_top])
            results["v2"]["portfolios"].append([s["symbol"] for s in v2_top])

            print(f"  Production: {prod_return:+.2f}%  |  Linear: {linear_return:+.2f}%  |  V2: {v2_return:+.2f}%")

        except Exception as e:
            print(f"  ❌ Error: {e}")
            continue

    # Summary
    print("\n" + "="*80)
    print("RESULTS SUMMARY")
    print("="*80)

    for method_name, method_data in results.items():
        if method_data["returns"]:
            avg_return = sum(method_data["returns"]) / len(method_data["returns"])
            total_return = sum(method_data["returns"])
            win_rate = sum(1 for r in method_data["returns"] if r > 0) / len(method_data["returns"]) * 100

            print(f"\n{method_name.upper()}:")
            print(f"  Average Return per period: {avg_return:+.2f}%")
            print(f"  Total Return: {total_return:+.2f}%")
            print(f"  Win Rate: {win_rate:.1f}%")
            print(f"  Periods tested: {len(method_data['returns'])}")

    print("\n" + "="*80)
    print("KEY FINDINGS:")

    # Compare
    if results["linear"]["returns"] and results["v2"]["returns"]:
        linear_avg = sum(results["linear"]["returns"]) / len(results["linear"]["returns"])
        v2_avg = sum(results["v2"]["returns"]) / len(results["v2"]["returns"])

        diff = v2_avg - linear_avg
        if abs(diff) < 0.5:
            print(f"  ≈ V2 and Linear perform similarly ({diff:+.2f}% difference)")
        elif diff > 0:
            print(f"  ✅ V2 OUTPERFORMS Linear by {diff:+.2f}% per period")
        else:
            print(f"  ⚠️  Linear OUTPERFORMS V2 by {abs(diff):+.2f}% per period")

    if results["production"]["returns"]:
        prod_avg = sum(results["production"]["returns"]) / len(results["production"]["returns"])
        linear_avg = sum(results["linear"]["returns"]) / len(results["linear"]["returns"])

        diff = prod_avg - linear_avg
        if diff < linear_avg * -0.1:  # More than 10% worse
            print(f"  ⚠️  Production formula UNDERPERFORMS Linear by {abs(diff):+.2f}%")
            print(f"      (Confirms the compound annualization bug is hurting performance)")

    print("\n")

    return results


if __name__ == "__main__":
    import sys

    # Allow command line arguments
    lookback_days = int(sys.argv[1]) if len(sys.argv) > 1 else 180
    num_stocks = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    rebalance_days = int(sys.argv[3]) if len(sys.argv) > 3 else 90

    test_scoring_methods(
        lookback_days=lookback_days,
        num_stocks=num_stocks,
        rebalance_days=rebalance_days
    )
