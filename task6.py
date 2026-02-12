# E-COMMERCE KPI DASHBOARD (TEXT OUTPUT)

original_price = 950.00
discount = 0.40
rating = 3.8

effective_price = original_price * (1 - discount)
revenue_loss = original_price - effective_price
satisfaction = (rating / 5) * 100

print("=" * 70)
print("E-COMMERCE KPI ANALYSIS & BUSINESS INSIGHTS")
print("=" * 70)

print("\n📊 PRICING STRATEGY ANALYSIS")
print("-" * 70)
print(f"✓ Original Price        : ${original_price:.2f}")
print(f"✓ Average Discount      : {int(discount*100)}%")
print(f"✓ Effective Price       : ${effective_price:.2f}")
print(f"✓ Revenue Loss / Unit   : ${revenue_loss:.2f}")

print("\n⚠️ CRITICAL INSIGHT:")
print("• Heavy discounting (40%) risks margin erosion")
print("• Indicates pricing or product-value issues")

print("\n⭐ CUSTOMER SATISFACTION ANALYSIS")
print("-" * 70)
print(f"✓ Average Rating        : {rating}/5")
print(f"✓ Satisfaction Level    : {satisfaction:.1f}%")
print("✓ Sentiment             : Average 🟠")

print("\n⚠️ BELOW-AVERAGE EXPERIENCE:")
print("• Discounts are not compensating for quality/service issues")

print("\n🔗 DISCOUNT vs RATING ANALYSIS")
print("-" * 70)
print(f"✓ Discount : {int(discount*100)}%")
print(f"✓ Rating   : {rating}")
print("✓ Risk     : CRITICAL")
print("  • High discount NOT improving satisfaction")
print("  • Root cause likely quality or fulfillment")

print("\n💡 STRATEGIC RECOMMENDATIONS")
print("-" * 70)
print("1. Reduce blanket discount from 40% → 25–30%")
print("2. Improve product quality & delivery to raise rating ≥ 4.3")
print(f"3. Recover margin loss of ${revenue_loss:.2f} per unit")
print("4. Introduce segment-based and loyalty discounts")

print("\n" + "=" * 70)
print("KPI DASHBOARD SUMMARY")
print("=" * 70)
print("       Metric           Value Status")
print(f"     Avg Price        ${original_price:.2f}      ⚠️")
print(f"      Discount           {int(discount*100)}%      🔴")
print(f"Effective Price        ${effective_price:.2f}      ⚠️")
print(f"        Rating          {rating}★      🟠")

print("\n📈 PROFIT SCENARIOS (1000 Units)")
print("-" * 70)
print(f"Current (40%)                 : ${effective_price*1000:,.0f}")
print(f"30% Discount                  : ${950*0.70*1000:,.0f}")
print(f"30% + 15% Volume              : ${(950*0.70*1.15)*1000:,.0f}")
print(f"25% + Better Rating           : ${(950*0.75*1.10)*1000:,.0f}")