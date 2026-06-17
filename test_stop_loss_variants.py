#!/usr/bin/env python3
"""
Test ALL combinations of profit targets and stop losses with weekly checks.
Find optimal YY% profit + XX% loss strategy.
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
    """NEW percentile-based scoring"""
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

def test_strategy(profit_target, stop_loss, max_hold_days, num_stocks=12):
    """
    Test strategy with:
    - profit_target% profit threshold (VARIABLE)
    - stop_loss% loss threshold (VARIABLE)
    - max_hold_days: mandatory rebalance after N days (VARIABLE)
    - Weekly checks (7 days minimum)
    """
    # Load cached dates
    cache = Path(CACHE_DIR)
    dates = sorted([f.name.split("-")[1:4] for f in cache.glob("portfolio-*.json")])
    dates = ["-".join(d) for d in dates]

    if len(dates) < 2:
        return None

    # Start
    start_date = dates[0]
    with open(cache / f"portfolio-{start_date}-200-500000.json") as f:
        start_stocks = json.load(f)["portfolio"]

    portfolio = [s["stock"] for s in score_new(start_stocks)[:num_stocks]]
    initial_value = sum(s["investment"] for s in portfolio)
    last_rebalance_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")

    returns = []
    rebalances = []
    profit_exits = 0
    loss_exits = 0
    max_hold_exits = 0

    for check_date in dates[1:]:
        check_dt = datetime.datetime.strptime(check_date, "%Y-%m-%d")
        days_held = (check_dt - last_rebalance_date).days

        # Only check weekly
        if days_held < 7:
            continue

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
            profit_exits += 1
        elif profit_pct <= stop_loss:
            should_rebalance = True
            reason = "stop_loss"
            loss_exits += 1
        elif days_held >= max_hold_days:
            should_rebalance = True
            reason = "max_hold"
            max_hold_exits += 1

        if should_rebalance:
            returns.append(profit_pct)
            rebalances.append({
                "date": check_date,
                "return": profit_pct,
                "days": days_held,
                "reason": reason
            })

            # Rebalance
            portfolio = [s["stock"] for s in score_new(current_data)[:num_stocks]]
            initial_value = sum(s["investment"] for s in portfolio)
            last_rebalance_date = check_dt

    if not returns:
        return None

    return {
        "returns": returns,
        "rebalances": rebalances,
        "profit_exits": profit_exits,
        "loss_exits": loss_exits,
        "max_hold_exits": max_hold_exits,
        "total_rebalances": len(returns),
        "avg_return": sum(returns) / len(returns),
        "total_return": sum(returns),
        "win_rate": sum(1 for r in returns if r > 0) / len(returns) * 100,
        "max_loss": min(returns),
    }

# Test ALL combinations
print("\n" + "="*80)
print("PROFIT TARGET + STOP LOSS OPTIMIZATION")
print("="*80)
print("\nFixed Parameters:")
print("  - Check Frequency: Weekly (7 days)")
print("  - Scoring: NEW percentile method")
print("\nVariable: YY% profit + XX% loss combinations")
print("="*80)

profit_targets = [1.0, 1.5, 2.0, 2.5, 3.0]
stop_losses = [-2.0, -3.0, -5.0, -7.0, -10.0]
max_hold_periods = [7, 14, 30, 60, 90]

results = []
total_tests = len(profit_targets) * len(stop_losses) * len(max_hold_periods)
test_num = 0

for profit_target in profit_targets:
    for stop_loss in stop_losses:
        for max_hold in max_hold_periods:
            test_num += 1
            label = f"+{profit_target:.1f}%/{stop_loss:+.1f}%/{max_hold}d"
            print(f"\n[{test_num}/{total_tests}] {label}...", end=" ")

            result = test_strategy(profit_target, stop_loss, max_hold)
            if result:
                results.append({
                    "profit_target": profit_target,
                    "stop_loss": stop_loss,
                    "max_hold": max_hold,
                    "label": label,
                    **result
                })
                print(f"✓ {result['total_rebalances']} trades "
                      f"({result['profit_exits']}P/{result['loss_exits']}L/{result['max_hold_exits']}H) "
                      f"| Avg {result['avg_return']:+.2f}% | Total {result['total_return']:+.2f}%")
            else:
                print("✗ No data")

# Sort and display top results
print("\n\n" + "="*80)
print("TOP 10 STRATEGIES (by Total Return)")
print("="*80)
print(f"\n{'Strategy':>20} | {'Trades':>6} | {'P/L/H Exits':>12} | "
      f"{'Avg':>7} | {'Total':>8} | {'Win%':>5} | {'MaxLoss':>8}")
print("-"*85)

sorted_results = sorted(results, key=lambda x: x["total_return"], reverse=True)[:10]

for r in sorted_results:
    exits = f"{r['profit_exits']}/{r['loss_exits']}/{r['max_hold_exits']}"
    print(f"{r['label']:>20} | {r['total_rebalances']:>6} | "
          f"{exits:>12} | {r['avg_return']:>+6.2f}% | "
          f"{r['total_return']:>+7.2f}% | {r['win_rate']:>4.1f}% | "
          f"{r['max_loss']:>+7.2f}%")

# Full table - just show summary by stop loss + max hold (profit target doesn't matter much)
print("\n\n" + "="*80)
print("GROUPED BY STOP LOSS & MAX HOLD (Profit target has minimal impact)")
print("="*80)

# Group by stop loss and max hold, show best profit target for each
grouped = {}
for r in results:
    key = (r['stop_loss'], r['max_hold'])
    if key not in grouped or r['total_return'] > grouped[key]['total_return']:
        grouped[key] = r

print(f"\n{'StopLoss':>9} | {'MaxHold':>8} | {'Best Profit':>11} | {'Trades':>6} | "
      f"{'Avg':>7} | {'Total':>8} | {'MaxLoss':>8}")
print("-"*80)

for (stop_loss, max_hold) in sorted(grouped.keys(), key=lambda x: (x[1], -x[0])):
    r = grouped[(stop_loss, max_hold)]
    print(f"{stop_loss:>+8.1f}% | {max_hold:>6}d | "
          f"{r['profit_target']:>+9.1f}% | {r['total_rebalances']:>6} | "
          f"{r['avg_return']:>+6.2f}% | {r['total_return']:>+7.2f}% | "
          f"{r['max_loss']:>+7.2f}%")

# Find best strategy
print("\n" + "="*80)
print("ANALYSIS")
print("="*80)

best_total = max(results, key=lambda x: x["total_return"])
best_avg = max(results, key=lambda x: x["avg_return"])
best_protection = max(results, key=lambda x: x["max_loss"])

print(f"\n✅ Best Total Return: {best_total['label']} "
      f"({best_total['total_return']:+.2f}%)")

print(f"\n✅ Best Avg Return/Trade: {best_avg['label']} "
      f"({best_avg['avg_return']:+.2f}%)")

print(f"\n🛡️  Best Downside Protection: {best_protection['label']} "
      f"(Max loss: {best_protection['max_loss']:+.2f}%)")

# Compare vs current strategy (2% profit / -10% loose stop / 90-day hold)
current_strategy = next((r for r in results
                        if r['profit_target'] == 2.0 and r['stop_loss'] == -10.0
                        and r['max_hold'] == 90), None)

if current_strategy:
    print(f"\n" + "="*80)
    print(f"IMPROVEMENT vs YOUR CURRENT STRATEGY ({current_strategy['label']})")
    print("="*80)
    print(f"\nCurrent strategy performance:")
    print(f"  Total Return: {current_strategy['total_return']:+.2f}%")
    print(f"  Avg Return:   {current_strategy['avg_return']:+.2f}%")
    print(f"  Trades:       {current_strategy['total_rebalances']}")
    print(f"  Max Loss:     {current_strategy['max_loss']:+.2f}%")

    print(f"\nTop 5 improvements:")
    for i, r in enumerate(sorted_results[:5], 1):
        if r['label'] == current_strategy['label']:
            continue
        diff_total = r["total_return"] - current_strategy["total_return"]
        diff_avg = r["avg_return"] - current_strategy["avg_return"]
        protected_loss = r["max_loss"] - current_strategy["max_loss"]

        print(f"\n{i}. {r['label']}:")
        print(f"   Total Return:  {diff_total:+.2f}% "
              f"({'✅' if diff_total > 0 else '⚠️'})")
        print(f"   Avg Return:    {diff_avg:+.2f}% "
              f"({'✅' if diff_avg > 0 else '⚠️'})")
        print(f"   Max Loss Protection: {protected_loss:+.2f}% "
              f"({'✅' if protected_loss > 0 else '⚠️'})")
        print(f"   Trade difference: {r['total_rebalances'] - current_strategy['total_rebalances']:+d}")

print("\n" + "="*80)
print("RECOMMENDATION")
print("="*80)

print(f"\nBased on your goal to 'book profit fast, okay to book loss too':")
print(f"\nIf you want BEST returns:")
print(f"  → Use {best_avg['label']} stop loss")
print(f"  → Gives {best_avg['avg_return']:+.2f}% per trade")

print(f"\nIf you want MAXIMUM protection:")
print(f"  → Use {best_protection['label']} stop loss")
print(f"  → Limits losses to {best_protection['max_loss']:+.2f}%")

print("\n" + "="*80)
