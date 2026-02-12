import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------- FIXED DATA ----------------
subcategory = [f"subcat_{i}" for i in range(1, 21)]

avg_price = np.array([
    240, 255, 260, 270, 275,
    280, 285, 290, 295, 300,
    305, 310, 315, 320, 325,
    330, 335, 340, 345, 350
])

avg_rating = np.array([
    4.06, 4.05, 3.96, 4.03, 4.04,
    3.98, 4.07, 3.94, 3.90, 4.12,
    3.95, 4.01, 3.92, 3.88, 3.99,
    4.05, 4.02, 3.93, 3.91, 4.10
])

count = np.array([
    45, 50, 48, 52, 49,
    55, 60, 47, 44, 62,
    51, 53, 46, 45, 58,
    61, 59, 50, 48, 64
])

grp = pd.DataFrame({
    "subcategory": subcategory,
    "avg_price": avg_price,
    "avg_rating": avg_rating,
    "count": count
})

# ---------------- SCATTER + REGRESSION ----------------
plt.figure(figsize=(10, 6))

sns.scatterplot(
    data=grp,
    x="avg_price",
    y="avg_rating",
    size="count",
    hue="count",
    sizes=(40, 400),
    palette="viridis",
    edgecolor="black",
    alpha=0.85
)

# regression line
coef = np.polyfit(np.log(grp["avg_price"]), grp["avg_rating"], 1)
x_line = np.linspace(grp["avg_price"].min(), grp["avg_price"].max(), 100)
y_line = coef[0] * np.log(x_line) + coef[1]
plt.plot(x_line, y_line)

plt.xscale("log")
plt.xlabel("Avg Price (log)")
plt.ylabel("Avg Rating")
plt.title("Avg Price vs Rating by Subcategory")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()

# ---------------- CORRELATION ----------------
pearson = np.corrcoef(np.log(grp["avg_price"]), grp["avg_rating"])[0, 1]
spearman = np.corrcoef(
    grp["avg_price"].rank(),
    grp["avg_rating"].rank()
)[0, 1]

print("Pearson (log):", round(pearson, 3))
print("Spearman:", round(spearman, 3))