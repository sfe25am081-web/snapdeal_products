import random
import math
import matplotlib.pyplot as plt

# Simulate data without numpy
random.seed(123)

price = [math.exp(random.gauss(5.5, 0.6)) for _ in range(1000)]
discount = [
    max(0, min(50, 20 - 0.003 * p + random.gauss(0, 2)))
    for p in price
]

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Scatter plot
axes[0].scatter(price, discount, alpha=0.5, s=30)
axes[0].set_title("Scatter plot (Price vs Discount)")
axes[0].set_xlabel("Price")
axes[0].set_ylabel("Discount (%)")

# 2D histogram (heatmap-like)
axes[1].hist2d(price, discount, bins=40)
axes[1].set_title("2D Histogram (Density)")
axes[1].set_xlabel("Price")
axes[1].set_ylabel("Discount (%)")
plt.colorbar(axes[1].collections[0], ax=axes[1])

plt.tight_layout()
plt.show()
plt.savefig("output.png")
plt.show()