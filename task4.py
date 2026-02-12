import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr

# -----------------------------
# Data simulation
# -----------------------------
np.random.seed(42)
n = 1000

df = pd.DataFrame({
    "Discount": np.random.uniform(0, 50, n),
})

df["Rating"] = np.clip(
    3 + 0.01 * df["Discount"] + np.random.normal(0, 1, n),
    1, 5
)

# -----------------------------
# Correlation
# -----------------------------
corr, p = pearsonr(df["Discount"], df["Rating"])
print(f"Correlation: {corr:.3f}, P-value: {p:.3f}")

# -----------------------------
# Discount bins
# -----------------------------
df["Discount_Bin"] = pd.cut(
    df["Discount"],
    [0, 10, 20, 30, 40, 50],
    labels=["0–10%", "10–20%", "20–30%", "30–40%", "40–50%"],
    include_lowest=True
)

avg_rating = (
    df.groupby("Discount_Bin", observed=True)["Rating"]
    .mean()
    .reset_index()
)

# -----------------------------
# BOTH PLOTS TOGETHER (FIX 🔥)
# -----------------------------
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# 1️⃣ Scatter plot
axes[0].scatter(df["Discount"], df["Rating"], alpha=0.4)
axes[0].set_title("Rating vs Discount")
axes[0].set_xlabel("Discount (%)")
axes[0].set_ylabel("Rating")
axes[0].grid(alpha=0.3)

# 2️⃣ Bar chart
sns.barplot(
    x="Discount_Bin",
    y="Rating",
    data=avg_rating,
    ax=axes[1]
)
axes[1].set_title("Average Rating by Discount Range")
axes[1].set_xlabel("Discount Range")
axes[1].set_ylabel("Average Rating")
axes[1].set_ylim(1, 5)

plt.tight_layout()
plt.show()

# -----------------------------
# Conclusion
# -----------------------------
print(
    "\nConclusion:",
    "Weak relationship between discount and rating"
    if abs(corr) < 0.3
    else "Noticeable correlation exists"
)