import pandas as pd

df = pd.DataFrame([
    {"Product": "A", "Price": 10.0, "Discount": 0.60, "Rating": 4.2},
    {"Product": "B", "Price": 15.0, "Discount": 0.05, "Rating": 2.7},
    {"Product": "C", "Price": 20.0, "Discount": 0.20, "Rating": 2.9},
])

def discount_text(d):
    if d > 0.5:
        return f"**{int(d*100)}%** 🟩 (green)"
    if d < 0.1:
        return f"**{int(d*100)}%** 🟥 (red)"
    return f"{int(d*100)}%"

def rating_text(r):
    if r < 3:
        return f"**{r}** 🟧 (orange)"
    return str(r)

print("| Product | Price    | Discount           | Rating              |")
print("| ------- | -------- | ------------------ | ------------------- |")

for _, row in df.iterrows():
    print(
        f"| {row['Product']}       "
        f"| `${row['Price']:.2f}` "
        f"| {discount_text(row['Discount']):18} "
        f"| {rating_text(row['Rating']):19} |"
    )