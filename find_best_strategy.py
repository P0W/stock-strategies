#!/usr/bin/env python3
"""
Find the best rebalancing strategy by testing multiple combinations.

Tests different combinations of:
- Profit target (when to take profit)
- Stop loss (when to cut losses)
- Max hold period (mandatory rebalance)
"""

import json
from pathlib import Path
import datetime

CACHE_DIR = "/cache/stock-strategies"

def percentile_rank(values):
    n = len(values)
    indexed = [(v, i) for i, v in enumerate(values)]
    sorted_vals = sorted(indexed, key=lambda x: x[0])
    ranks = [0] * n
    for rank_pos, (_, orig_idx) in enumerate(sorted_vals):
        percentile = (rank_pos / (n - 1)) * 100 if n > 1 else 50
        ranks[orig_idx] = percentile
    return ranks

def score_new(stocks):
    """NEW percentile scoring."""
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

def test_strategy(profit_target, stop_loss, max_hold_days, num_stocks=12):
    """
    Test a specific rebalancing strategy.

    Args:
        profit_target: % profit to trigger rebalance (e.g., 1.5)
        stop_loss: % loss to trigger rebalance (e.g., -5)
        max_hold_days: Max days before mandatory rebalance

    Returns:
        dict with performance metrics
    """
    # Start
    start_date = dates[0]
    with open(cache / f"portfolio-{start_date}-200-500000.json") as f:
        start_stocks = json.load(f)["portfolio"]

    portfolio = [s["stock"] for s in score_new(start_stocks)[:num_stocks]]
    initial_value = sum(s["investment"] for s in portfolio)
    last_rebalance_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")

    rebalances = []
    total_return = 0

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

        if profit_pct >= profit_target:
            should_rebalance = True
            reason = "profit"
        elif profit_pct <= stop_loss:
            should_rebalance = True
            reason = "stop_loss"
        elif days_held >= max_hold_days:
            should_rebalance = True
            reason = "max_hold"

        if should_rebalance:
            rebalances.append({
                "date": check_date,
                "return": profit_pct,
                "days": days_held,
                "reason": reason
            })
            total_return += profit_pct

            # Rebalance
            portfolio = [s["stock"] for s in score_new(current_data)[:num_stocks]]
            initial_value = sum(s["investment"] for s in portfolio)
            last_rebalance_date = check_dt

    if not rebalances:
        return None

    # Calculate metrics
    returns = [r["return"] for r in rebalances]
    avg_return = sum(returns) / len(returns)
    wins = sum(1 for r in returns if r > 0)
    win_rate = wins / len(returns) * 100

    # Count reasons
    profit_exits = sum(1 for r in rebalances if r["reason"] == "profit")
    stop_exits = sum(1 for r in rebalances if r["reason"] == "stop_loss")
    max_hold_exits = sum(1 for r in rebalances if r["reason"] == "max_hold")

    return {
        "profit_target": profit_target,
        "stop_loss": stop_loss,
        "max_hold_days": max_hold_days,
        "rebalances": len(rebalances),
        "avg_return": avg_return,
        "total_return": total_return,
        "win_rate": win_rate,
        "profit_exits": profit_exits,
        "stop_exits": stop_exits,
        "max_hold_exits": max_hold_exits,
        "avg_days_held": sum(r["days"] for r in rebalances) / len(rebalances)
    }


# Test multiple strategies
print("\n" + "="*80)
print("FINDING BEST REBALANCING STRATEGY")
print("="*80)
print(f"\nTesting on {len(dates)} periods ({dates[0]} to {dates[-1]})")
print("Using NEW percentile scoring method")
print("\n" + "="*80)

strategies = []

# Define strategies to test
profit_targets = [1.0, 1.5, 2.0, 3.0]
stop_losses = [-3.0, -5.0, -7.0, -10.0]
max_holds = [7, 14, 30, 60]

print("\nTesting strategies...")
count = 0
total = len(profit_targets) * len(stop_losses) * len(max_holds)

for profit in profit_targets:
    for stop in stop_losses:
        for max_hold in max_holds:
            count += 1
            result = test_strategy(profit, stop, max_hold)
            if result:
                strategies.append(result)
                if count % 10 == 0:
                    print(f"  Tested {count}/{total} strategies...")

print(f"\n✅ Tested {len(strategies)} valid strategies\n")

# Sort by total return
strategies.sort(key=lambda x: x["total_return"], reverse=True)

# Show top 10
print("="*80)
print("TOP 10 STRATEGIES (by total return)")
print("="*80)
print(f"{'Rank':<5} {'Profit':<7} {'Stop':<7} {'MaxHold':<9} {'Rebal':<6} {'AvgRet':<8} {'Total':<8} {'Win%':<6} {'AvgDays':<8}")
print("-"*80)

for i, s in enumerate(strategies[:10], 1):
    print(f"{i:<5} {s['profit_target']:>6.1f}% {s['stop_loss']:>6.1f}% {s['max_hold_days']:>7}d "
          f"{s['rebalances']:>5} {s['avg_return']:>+7.2f}% {s['total_return']:>+7.2f}% "
          f"{s['win_rate']:>5.1f}% {s['avg_days_held']:>7.1f}")

# Analyze best strategy
best = strategies[0]
print("\n" + "="*80)
print("BEST STRATEGY DETAILS")
print("="*80)
print(f"\nConfiguration:")
print(f"  Profit target:   {best['profit_target']:+.1f}% (take profit)")
print(f"  Stop loss:       {best['stop_loss']:+.1f}% (cut losses)")
print(f"  Max hold:        {best['max_hold_days']} days (mandatory rebalance)")

print(f"\nPerformance:")
print(f"  Total rebalances:  {best['rebalances']}")
print(f"  Average return:    {best['avg_return']:+.2f}% per rebalance")
print(f"  Total return:      {best['total_return']:+.2f}%")
print(f"  Win rate:          {best['win_rate']:.1f}%")
print(f"  Avg hold time:     {best['avg_days_held']:.1f} days")

print(f"\nExit breakdown:")
print(f"  Profit targets hit:  {best['profit_exits']} times ({best['profit_exits']/best['rebalances']*100:.1f}%)")
print(f"  Stop losses hit:     {best['stop_exits']} times ({best['stop_exits']/best['rebalances']*100:.1f}%)")
print(f"  Max hold forced:     {best['max_hold_exits']} times ({best['max_hold_exits']/best['rebalances']*100:.1f}%)")

# Compare to your current strategy
print("\n" + "="*80)
print("COMPARISON TO YOUR CURRENT STRATEGY (2% profit / 90-day)")
print("="*80)

current = test_strategy(2.0, -100, 90)  # Your current (no stop loss, just 90-day)
if current:
    print(f"\nCurrent strategy:")
    print(f"  Total return:   {current['total_return']:+.2f}%")
    print(f"  Avg return:     {current['avg_return']:+.2f}%")
    print(f"  Rebalances:     {current['rebalances']}")
    print(f"  Win rate:       {current['win_rate']:.1f}%")

    print(f"\nBest strategy:")
    print(f"  Total return:   {best['total_return']:+.2f}%  (Δ {best['total_return'] - current['total_return']:+.2f}%)")
    print(f"  Avg return:     {best['avg_return']:+.2f}%  (Δ {best['avg_return'] - current['avg_return']:+.2f}%)")
    print(f"  Rebalances:     {best['rebalances']}  (Δ {best['rebalances'] - current['rebalances']:+d})")
    print(f"  Win rate:       {best['win_rate']:.1f}%  (Δ {best['win_rate'] - current['win_rate']:+.1f}%)")

    improvement = best['total_return'] - current['total_return']
    if improvement > 2:
        print(f"\n✅ SIGNIFICANT IMPROVEMENT: +{improvement:.2f}% total return")
    elif improvement > 0:
        print(f"\n✓ Better: +{improvement:.2f}% improvement")
    else:
        print(f"\n⚠️  Worse by {abs(improvement):.2f}%")

print("\n")
