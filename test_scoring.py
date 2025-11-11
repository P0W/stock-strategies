#!/usr/bin/env python3
"""
Single script to test momentum scoring methods on real Azure data.

Usage:
    python test_scoring.py [days_back] [num_stocks] [rebalance_days]

Example:
    python test_scoring.py 365 12 90
"""

import json
import os
import sys
import datetime
import requests
from pathlib import Path

# Configuration
API_BASE = "https://stocks.eastus.cloudapp.azure.com"
CACHE_DIR = "/cache/stock-strategies"
TRIAL_USER = "trialuser"
TRIAL_PASS_HASH = "1de04c49ce1b1bd6c8ce2af8f69213c3013cf2dbf4309cad043a4074c97a5156"


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


def login_trial_user():
    """Login as trial user and return session."""
    session = requests.Session()
    url = f"{API_BASE}/login"
    payload = {"username": TRIAL_USER, "hashedPassword": TRIAL_PASS_HASH}

    print(f"🔐 Logging in as {TRIAL_USER}...")
    resp = session.post(url, json=payload, timeout=30)

    if resp.status_code == 200:
        print(f"✅ Logged in successfully")
        return session
    else:
        print(f"❌ Login failed: {resp.status_code}")
        return None


def get_cached_or_fetch(session, endpoint, cache_file):
    """Get data from cache or fetch from API."""
    cache_path = Path(CACHE_DIR) / cache_file

    # Try cache first
    if cache_path.exists():
        with open(cache_path, 'r') as f:
            return json.load(f)

    # Fetch from API
    url = f"{API_BASE}{endpoint}"
    try:
        resp = session.get(url, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            # Cache it
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_path, 'w') as f:
                json.dump(data, f)
            return data
    except Exception as e:
        print(f"⚠️  Failed to fetch {endpoint}: {e}")

    return None


def fetch_portfolio_data(session, date_str, num_stocks=200, investment=500000):
    """Fetch portfolio data for a date (contains full stock info)."""
    cache_file = f"portfolio-{date_str}-{num_stocks}-{investment}.json"
    endpoint = f"/portfolio/{date_str}/{num_stocks}/{investment}"

    data = get_cached_or_fetch(session, endpoint, cache_file)
    if data and "portfolio" in data:
        return data["portfolio"]
    return None


def score_old_production(stocks):
    """OLD: Current get_stocks.py with compound annualization bug."""
    scored = []
    for stock in stocks:
        try:
            r1y = stock["returns"]["1y"]["return"]
            r1mo = 100.0 * ((1 + stock["returns"]["1mo"]["return"] / 100.0) ** 12 - 1)
            r1w = 100.0 * ((1 + stock["returns"]["1w"]["return"] / 100.0) ** 52 - 1)

            time_weights = [0.2, 0.3, 0.5]
            score = r1y * time_weights[0] + r1mo * time_weights[1] + r1w * time_weights[2]

            scored.append({"symbol": stock["symbol"], "score": score, "stock": stock})
        except (KeyError, TypeError, ZeroDivisionError):
            continue

    return sorted(scored, key=lambda x: x["score"], reverse=True)


def score_new_percentile(stocks):
    """NEW: Percentile ranking (proposed improvement)."""
    symbols = []
    returns_1y = []
    returns_1mo = []
    stocks_list = []

    for stock in stocks:
        try:
            symbols.append(stock["symbol"])
            returns_1y.append(stock["returns"]["1y"]["return"])
            returns_1mo.append(stock["returns"]["1mo"]["return"])
            stocks_list.append(stock)
        except (KeyError, TypeError):
            continue

    rank_1y = percentile_rank(returns_1y)
    rank_1mo = percentile_rank(returns_1mo)

    scored = []
    for i, symbol in enumerate(symbols):
        score = 0.6 * rank_1y[i] + 0.4 * rank_1mo[i]
        scored.append({"symbol": symbol, "score": score, "stock": stocks_list[i]})

    return sorted(scored, key=lambda x: x["score"], reverse=True)


def calculate_return(portfolio, future_prices):
    """Calculate return for a portfolio."""
    initial = sum(s["stock"]["investment"] for s in portfolio)
    final = sum(future_prices.get(s["symbol"], s["stock"]["price"]) * s["stock"]["shares"]
                for s in portfolio)
    return ((final - initial) / initial * 100) if initial > 0 else 0


def generate_test_dates(days_back, rebalance_days):
    """Generate test date pairs."""
    end = datetime.datetime.now() - datetime.timedelta(days=1)
    start = end - datetime.timedelta(days=days_back)

    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime("%Y-%m-%d"))
        current += datetime.timedelta(days=1)

    # Create rebalance pairs
    pairs = []
    for i in range(0, len(dates) - rebalance_days, rebalance_days // 3):  # Sample every 1/3 period
        if i + rebalance_days < len(dates):
            pairs.append((dates[i], dates[i + rebalance_days]))

    return pairs


def run_comparison(days_back=365, num_stocks=12, rebalance_days=90):
    """Run the complete comparison."""
    print("\n" + "="*80)
    print("MOMENTUM SCORING COMPARISON - LIVE AZURE DATA")
    print("="*80)
    print(f"\nConfiguration:")
    print(f"  API: {API_BASE}")
    print(f"  Cache: {CACHE_DIR}")
    print(f"  Lookback: {days_back} days")
    print(f"  Portfolio: {num_stocks} stocks")
    print(f"  Rebalance: every {rebalance_days} days")

    # Login
    session = login_trial_user()
    if not session:
        return None

    # Generate test dates
    print(f"\n📅 Generating test periods...")
    test_pairs = generate_test_dates(days_back, rebalance_days)
    print(f"✅ Found {len(test_pairs)} test periods")

    # Run tests
    print(f"\n🧪 Testing scoring methods...")
    print("-"*80)

    results = {"old": [], "new": []}
    tested = 0

    for idx, (start_date, end_date) in enumerate(test_pairs, 1):
        # Fetch data
        start_stocks = fetch_portfolio_data(session, start_date, 200, 500000)
        end_stocks = fetch_portfolio_data(session, end_date, 200, 500000)

        if not start_stocks or not end_stocks:
            continue

        tested += 1

        # Get end prices
        end_prices = {s["symbol"]: s["price"] for s in end_stocks}

        # Score both ways
        old_scored = score_old_production(start_stocks)[:num_stocks]
        new_scored = score_new_percentile(start_stocks)[:num_stocks]

        # Calculate returns
        old_return = calculate_return(old_scored, end_prices)
        new_return = calculate_return(new_scored, end_prices)

        results["old"].append(old_return)
        results["new"].append(new_return)

        # Show progress
        if tested % 5 == 1 or tested == len(test_pairs):
            print(f"Period {tested}: {start_date} → {end_date}")
            print(f"  OLD: {old_return:+.2f}%  |  NEW: {new_return:+.2f}%")

    if tested == 0:
        print("\n❌ No data available - check API access")
        return None

    # Analysis
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)

    for name, returns in [("OLD (Production Bug)", results["old"]),
                          ("NEW (Percentile)", results["new"])]:
        avg = sum(returns) / len(returns)
        total = sum(returns)
        wins = sum(1 for r in returns if r > 0)
        win_rate = wins / len(returns) * 100

        print(f"\n{name}:")
        print(f"  Average return/period:  {avg:+7.2f}%")
        print(f"  Total return:           {total:+7.2f}%")
        print(f"  Win rate:               {win_rate:7.1f}% ({wins}/{len(returns)})")
        print(f"  Best:  {max(returns):+.2f}%  |  Worst: {min(returns):+.2f}%")

    # Head-to-head
    print("\n" + "="*80)
    print("COMPARISON")
    print("="*80)

    old_avg = sum(results["old"]) / len(results["old"])
    new_avg = sum(results["new"]) / len(results["new"])
    diff = new_avg - old_avg

    new_wins = sum(1 for i in range(len(results["old"]))
                   if results["new"][i] > results["old"][i])

    print(f"\n📊 NEW vs OLD:")
    if abs(diff) < 0.3:
        print(f"   ≈ SIMILAR performance ({diff:+.2f}%)")
    elif diff > 0:
        print(f"   ✅ NEW WINS by {diff:+.2f}% per period")
        print(f"      Annualized: {diff * (365/rebalance_days):+.2f}%")
    else:
        print(f"   ❌ OLD WINS by {abs(diff):+.2f}% per period")

    print(f"\n   Head-to-head: NEW wins {new_wins}/{len(results['old'])} times ({new_wins/len(results['old'])*100:.1f}%)")

    # Recommendation
    print("\n" + "="*80)
    print("INTEGRATION PROPOSAL")
    print("="*80)

    if diff > 0.5:
        print("\n✅ RECOMMEND: Switch to NEW scoring")
        print_integration_plan()
    elif diff > -0.3:
        print("\n✓ VIABLE: NEW scoring is comparable or better")
        print_integration_plan()
    else:
        print("\n⚠️  OLD scoring performs better on this data")
        print("   Recommend more testing or keeping current formula")

    print("\n")
    return results


def print_integration_plan():
    """Print the integration proposal."""
    print("\n📝 Integration Steps:")
    print("""
1. BACKUP current get_stocks.py

2. ADD percentile_rank function to get_stocks.py:

   def percentile_rank(values):
       n = len(values)
       indexed = [(v, i) for i, v in enumerate(values)]
       sorted_vals = sorted(indexed, key=lambda x: x[0])
       ranks = [0] * n
       for rank_pos, (_, orig_idx) in enumerate(sorted_vals):
           percentile = (rank_pos / (n - 1)) * 100 if n > 1 else 50
           ranks[orig_idx] = percentile
       return ranks

3. REPLACE composite_score() with new version:

   def composite_score_v2(all_stocks_data):
       # Extract returns
       returns_1y = [s["returns"]["1y"]["return"] for s in all_stocks_data]
       returns_1mo = [s["returns"]["1mo"]["return"] for s in all_stocks_data]

       # Percentile rank
       rank_1y = percentile_rank(returns_1y)
       rank_1mo = percentile_rank(returns_1mo)

       # Calculate scores
       scores = []
       for i, stock in enumerate(all_stocks_data):
           score = 0.6 * rank_1y[i] + 0.4 * rank_1mo[i]
           stock["composite_score"] = score
           scores.append(stock)

       return sorted(scores, key=lambda x: x["composite_score"], reverse=True)

4. UPDATE getStockList() at line 290:

   # OLD:
   # results = sorted(results, key=lambda x: x["composite_score"], reverse=True)

   # NEW:
   results = composite_score_v2(results)

5. TEST on staging first, then deploy

6. MONITOR performance for 1-2 weeks
""")


if __name__ == "__main__":
    days_back = int(sys.argv[1]) if len(sys.argv) > 1 else 365
    num_stocks = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    rebalance_days = int(sys.argv[3]) if len(sys.argv) > 3 else 90

    run_comparison(days_back, num_stocks, rebalance_days)
