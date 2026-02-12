import pandas as pd
import numpy as np

# Data generate
np.random.seed(42)
dates = pd.date_range(start="2025-01-01", periods=90, freq="D")
discounts = np.random.uniform(10, 30, 90)

df = pd.DataFrame({
    "date": dates,
    "discount": discounts
})

# Monthly average
df["month"] = df["date"].dt.strftime("%b")
monthly_avg = df.groupby("month")["discount"].mean()

# ASCII graph print
print("\nDiscount (%) Trend\n")

max_val = 30
scale = 1  # height scale

for value in range(max_val, 9, -5):
    line = f"{value:>2} | "
    for avg in monthly_avg:
        if avg >= value:
            line += " /\  "
        else:
            line += "     "
    print(line)

print("   -----------------------------------------")
print("      ", end="")
for m in monthly_avg.index:
    print(f"{m:^5}", end="")
print()