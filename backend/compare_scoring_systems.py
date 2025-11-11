"""
Compare Old vs New Momentum Scoring Systems

This script demonstrates the differences between:
- Old: Compound annualization, double-weighted VWAP, no z-score normalization
- New: Percentile ranking, simple weights, aligned time periods
"""

import json
import logging
import sys

logging.basicConfig(level=logging.INFO)


def compare_systems(old_scores_file=None):
    """
    Compare old and new scoring systems.

    Args:
        old_scores_file: JSON file with stocks scored by old system
    """
    # Example: Show the calculation difference for a sample stock
    sample_stock = {
        "symbol": "RELIANCE",
        "price": 2500,
        "returns": {
            "1y": {"return": 20, "vwap": 2300, "rsi": 60},
            "1mo": {"return": 8, "vwap": 2450, "rsi": 65},
            "1w": {"return": 5, "vwap": 2480, "rsi": 70},
        }
    }

    print("\n" + "="*80)
    print("SCORING SYSTEM COMPARISON: RELIANCE Example")
    print("="*80)

    # OLD SYSTEM CALCULATION
    print("\n📊 OLD SYSTEM:")
    print("-" * 80)

    # Annualized returns (compound)
    old_1y_return = sample_stock["returns"]["1y"]["return"]
    old_1mo_annualized = 100.0 * ((1 + sample_stock["returns"]["1mo"]["return"] / 100.0) ** 12 - 1)
    old_1w_annualized = 100.0 * ((1 + sample_stock["returns"]["1w"]["return"] / 100.0) ** 52 - 1)

    print(f"Returns (annualized):")
    print(f"  1-year:  {old_1y_return:.1f}%")
    print(f"  1-month: {sample_stock['returns']['1mo']['return']:.1f}% → {old_1mo_annualized:.1f}% (compounded 12x) ⚠️")
    print(f"  1-week:  {sample_stock['returns']['1w']['return']:.1f}% → {old_1w_annualized:.1f}% (compounded 52x) ⚠️⚠️")

    # Time weights
    time_weights = [0.2, 0.3, 0.5]
    old_returns_component = (
        old_1y_return * time_weights[0] +
        old_1mo_annualized * time_weights[1] +
        old_1w_annualized * time_weights[2]
    )

    print(f"\nWeighted returns component:")
    print(f"  {old_1y_return:.1f}*0.2 + {old_1mo_annualized:.1f}*0.3 + {old_1w_annualized:.1f}*0.5")
    print(f"  = {old_returns_component:.1f} (dominated by 1w!)")

    # VWAP (double weighted)
    weighted_vwap = [0.2, 0.3, 0.5]
    price = sample_stock["price"]
    vwap_1y = sample_stock["returns"]["1y"]["vwap"]
    vwap_1mo = sample_stock["returns"]["1mo"]["vwap"]
    vwap_1w = sample_stock["returns"]["1w"]["vwap"]

    old_vwap_1y = (price - vwap_1y) * weighted_vwap[0] / price
    old_vwap_1mo = (price - vwap_1mo) * weighted_vwap[1] / price
    old_vwap_1w = (price - vwap_1w) * weighted_vwap[2] / price

    old_vwap_component = (
        old_vwap_1y * time_weights[0] +
        old_vwap_1mo * time_weights[1] +
        old_vwap_1w * time_weights[2]
    )

    print(f"\nVWAP component (double weighted):")
    print(f"  First weight applied: {weighted_vwap}")
    print(f"  Second weight applied: {time_weights}")
    print(f"  Effective weights: [0.04, 0.09, 0.25] (quadratic!) ⚠️")
    print(f"  Component value: {old_vwap_component:.4f}")

    # RSI
    old_rsi_component = (
        sample_stock["returns"]["1y"]["rsi"] * time_weights[0] +
        sample_stock["returns"]["1mo"]["rsi"] * time_weights[1] +
        sample_stock["returns"]["1w"]["rsi"] * time_weights[2]
    )
    print(f"\nRSI component (raw values):")
    print(f"  {sample_stock['returns']['1y']['rsi']}*0.2 + {sample_stock['returns']['1mo']['rsi']}*0.3 + {sample_stock['returns']['1w']['rsi']}*0.5")
    print(f"  = {old_rsi_component:.1f}")

    # Final score
    old_composite = (
        0.4 * old_returns_component +
        0.3 * old_vwap_component +
        0.3 * old_rsi_component
    )

    print(f"\nFinal composite score:")
    print(f"  0.4*{old_returns_component:.1f} + 0.3*{old_vwap_component:.4f} + 0.3*{old_rsi_component:.1f}")
    print(f"  = {old_composite:.2f}")
    print(f"\n⚠️ Problem: Scale mismatch! Returns ~1600, VWAP ~0.03, RSI ~67")
    print(f"  → Returns dominate completely (640 vs 0.01 vs 20)")
    print(f"  → Declared weights (40/30/30) are meaningless!")

    # NEW SYSTEM CALCULATION
    print("\n\n📊 NEW SYSTEM:")
    print("-" * 80)

    # Simple returns (no annualization for demo - would use 3mo in production)
    new_3mo_return = 15  # Would fetch real 3mo data
    new_1mo_return = sample_stock["returns"]["1mo"]["return"]

    print(f"Returns (raw, no compound annualization):")
    print(f"  3-month: {new_3mo_return:.1f}%")
    print(f"  1-month: {new_1mo_return:.1f}%")

    # VWAP (single weight)
    new_vwap_3mo = 2350  # Would use 3mo VWAP
    new_price_vs_vwap = ((price - new_vwap_3mo) / new_vwap_3mo) * 100

    print(f"\nVWAP analysis:")
    print(f"  Current price: ₹{price}")
    print(f"  3-month VWAP: ₹{new_vwap_3mo}")
    print(f"  Premium: {new_price_vs_vwap:.1f}%")

    # RSI
    new_rsi = sample_stock["returns"]["1mo"]["rsi"]
    print(f"\nRSI:")
    print(f"  1-month RSI: {new_rsi}")

    # Percentile ranking (simulated with 3 stocks)
    print(f"\nPercentile ranking (across all 200 stocks):")
    print(f"  Assume RELIANCE ranks:")
    rank_3mo = 85  # 85th percentile in 3mo returns
    rank_1mo = 75  # 75th percentile in 1mo returns
    rank_vwap = 80  # 80th percentile in price vs VWAP
    print(f"  - 3-month return: {rank_3mo}th percentile")
    print(f"  - 1-month return: {rank_1mo}th percentile")
    print(f"  - Price vs VWAP: {rank_vwap}th percentile")

    # Weighted score
    new_base_score = (
        0.5 * rank_3mo +
        0.3 * rank_1mo +
        0.2 * rank_vwap
    )

    print(f"\nWeighted base score:")
    print(f"  0.5*{rank_3mo} + 0.3*{rank_1mo} + 0.2*{rank_vwap}")
    print(f"  = {new_base_score:.1f}")

    # RSI filter
    rsi_penalty = 1.0 if 30 <= new_rsi <= 70 else 0.5
    rsi_status = "neutral" if rsi_penalty == 1.0 else "overbought"
    new_final_score = new_base_score * rsi_penalty

    print(f"\nRSI filter:")
    print(f"  RSI = {new_rsi} → Status: {rsi_status}")
    print(f"  Penalty: {rsi_penalty}x")
    print(f"\nFinal momentum score: {new_final_score:.1f}/100")

    print(f"\n✅ All components on same 0-100 scale")
    print(f"  → Weights (50/30/20) work as intended!")
    print(f"  → Easy to interpret: '{new_final_score:.0f}/100 = Top {100-new_final_score:.0f}% of stocks'")

    # COMPARISON SUMMARY
    print("\n\n" + "="*80)
    print("KEY DIFFERENCES SUMMARY")
    print("="*80)

    comparison_table = [
        ["Aspect", "Old System", "New System", "Winner"],
        ["-"*20, "-"*25, "-"*25, "-"*10],
        ["Annualization", "Compound (5% → 1167%)", "None (raw returns)", "NEW ✅"],
        ["VWAP weighting", "Double (quadratic)", "Single (linear)", "NEW ✅"],
        ["Normalization", "None (z-score unused)", "Percentile ranking", "NEW ✅"],
        ["Scale", "Mixed (0.01 to 1600)", "Uniform (0-100)", "NEW ✅"],
        ["Interpretability", "Hard to explain", "Easy (percentile)", "NEW ✅"],
        ["Components", "3 periods × 3 metrics", "2 periods + confirmation", "NEW ✅"],
        ["Strategy alignment", "Mismatched", "3mo=quarterly, 1mo=weekly", "NEW ✅"],
    ]

    for row in comparison_table:
        print(f"{row[0]:<22} {row[1]:<27} {row[2]:<27} {row[3]:<10}")

    print("\n" + "="*80)
    print("RECOMMENDATION: Adopt NEW system for better rankings")
    print("="*80)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        compare_systems(sys.argv[1])
    else:
        compare_systems()
