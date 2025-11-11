#!/usr/bin/env python3
"""
Test scoring methods with ACTUAL rebalancing strategy:
- Weekly check: if profit >= 2%, rebalance
- Otherwise: hold until 90 days, then mandatory rebalance
"""

import json
import requests
from pathlib import Path
import datetime

API_BASE = "https://stocks.eastus.cloudapp.azure.com"
CACHE_DIR = "/cache/stock-strategies"

def login():
    session = requests.Session()
    resp = session.post(f"{API_BASE}/login", json={
        "username": "trialuser",
        "hashedPassword": "1de04c49ce1b1bd6c8ce2af8f69213c3013cf2dbf4309cad043a4074c97a5156"
    }, timeout=30)
    return session if resp.status_code == 200 else None

def percentile_rank(values):
    n = len(values)
    indexed = [(v, i) for i, v in enumerate(values)]
    sorted_vals = sorted(indexed, key=lambda x: x[0])
    ranks = [0] * n
    for rank_pos, (_, orig_idx) in enumerate(sorted_vals):
        percentile = (rank_pos / (n - 1)) * 100 if n > 1 else 50
        ranks[orig_idx] = percentile
    return ranks

def score_old(stocks):
    scored = []
    for s in stocks:
        try:
            r1y = s["returns"]["1y"]["return"]
            r1mo = 100.0 * ((1 + s["returns"]["1mo"]["return"] / 100.0) ** 12 - 1)
            r1w = 100.0 * ((1 + s["returns"]["1w"]["return"] / 100.0) ** 52 - 1)
            score = r1y * 0.2 + r1mo * 0.3 + r1w * 0.5
            scored.append({"symbol": s["symbol"], "score": score, "stock": s})
        except:
            continue
    return sorted(scored, key=lambda x: x["score"], reverse=True)

def score_new(stocks):
    symbols, r1y, r1mo, stocks_list = [], [], [], []
    for s in stocks:
        try:
            symbols.append(s["symbol"])
            r1y.append(s["returns"]["1y"]["return"])
            r1mo.append(s["returns"]["1mo"]["return"])
            stocks_list.append(s)
        except:
            continue

    rank_1y = percentile_rank(r1y)
    rank_1mo = percentile_rank(r1mo)

    scored = []
    for i, symbol in enumerate(symbols):
        score = 0.6 * rank_1y[i] + 0.4 * rank_1mo[i]
        scored.append({"symbol": symbol, "score": score, "stock": stocks_list[i]})

    return sorted(scored, key=lambda x: x["score"], reverse=True)

# Load cached dates
cache = Path(CACHE_DIR)
dates = sorted([f.name.split("-")[1:4] for f in cache.glob("portfolio-*.json")])
dates = ["-".join(d) for d in dates]

print("\n" + "="*80)
print("TESTING WITH YOUR ACTUAL STRATEGY")
print("="*80)
print("\nStrategy: Weekly check for 2% profit OR 90-day mandatory rebalance")
print(f"Data: {len(dates)} monthly snapshots from {dates[0]} to {dates[-1]}")
print("="*80)

# Simulate both scoring methods
results = {"old": {"returns": [], "rebalances": []},
           "new": {"returns": [], "rebalances": []}}

for method_name, score_func in [("OLD", score_old), ("NEW", score_new)]:
    print(f"\n\n🧪 Testing {method_name} scoring method...")
    print("-"*80)

    # Start
    start_date = dates[0]
    with open(cache / f"portfolio-{start_date}-200-500000.json") as f:
        start_stocks = json.load(f)["portfolio"]

    portfolio = [s["stock"] for s in score_func(start_stocks)[:12]]
    initial_value = sum(s["investment"] for s in portfolio)
    last_rebalance_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")

    print(f"\nStart {start_date}: ₹{initial_value:,.0f}")

    rebalance_count = 0

    for check_date in dates[1:]:
        check_dt = datetime.datetime.strptime(check_date, "%Y-%m-%d")
        days_held = (check_dt - last_rebalance_date).days

        # Load current data
        with open(cache / f"portfolio-{check_date}-200-500000.json") as f:
            current_data = json.load(f)["portfolio"]

        current_prices = {s["symbol"]: s["price"] for s in current_data}

        # Calculate value
        current_value = sum(
            s["shares"] * current_prices.get(s["symbol"], s["price"])
            for s in portfolio
        )
        profit_pct = (current_value - initial_value) / initial_value * 100

        # Rebalancing decision
        should_rebalance = False
        reason = ""

        if days_held >= 7 and profit_pct >= 2.0:
            should_rebalance = True
            reason = f"✅ Profit: {profit_pct:+.2f}%"
        elif days_held >= 90:
            should_rebalance = True
            reason = f"📅 Mandatory: {days_held}d"

        if should_rebalance:
            rebalance_count += 1
            print(f"{check_date} (Day {days_held:3}): {reason:25} → Return: {profit_pct:+.2f}%")

            results[method_name.lower()]["returns"].append(profit_pct)
            results[method_name.lower()]["rebalances"].append({
                "date": check_date,
                "return": profit_pct,
                "days": days_held,
                "reason": reason
            })

            # Rebalance
            portfolio = [s["stock"] for s in score_func(current_data)[:12]]
            initial_value = sum(s["investment"] for s in portfolio)
            last_rebalance_date = check_dt

    print(f"\nTotal rebalances: {rebalance_count}")

# Compare
print("\n\n" + "="*80)
print("COMPARISON")
print("="*80)

for method in ["old", "new"]:
    name = method.upper()
    returns = results[method]["returns"]

    if returns:
        avg = sum(returns) / len(returns)
        wins = sum(1 for r in returns if r > 0)
        win_rate = wins / len(returns) * 100

        print(f"\n{name}:")
        print(f"  Rebalances: {len(returns)}")
        print(f"  Avg return: {avg:+.2f}% per rebalance")
        print(f"  Win rate:   {win_rate:.1f}% ({wins}/{len(returns)})")
        print(f"  Total:      {sum(returns):+.2f}%")

# Head-to-head
if results["old"]["returns"] and results["new"]["returns"]:
    old_avg = sum(results["old"]["returns"]) / len(results["old"]["returns"])
    new_avg = sum(results["new"]["returns"]) / len(results["new"]["returns"])

    print(f"\n{'='*80}")
    print(f"VERDICT:")
    print(f"{'='*80}")

    diff = new_avg - old_avg
    if abs(diff) < 0.5:
        print(f"\n≈ Both methods perform similarly ({diff:+.2f}% difference)")
        print(f"  → Scoring method doesn't matter much for your strategy!")
    elif diff > 0:
        print(f"\n✅ NEW scores better by {diff:+.2f}% per rebalance")
    else:
        print(f"\n⚠️  OLD scores better by {abs(diff):+.2f}% per rebalance")
