import time
import re
from datetime import datetime
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ===================== CONFIG =====================
OUTPUT_CSV = "snapdeal_products.csv"
HEADLESS = False
WAIT_TIME = 10
MAX_PRODUCTS = 10

BASE_SECTIONS = {
    "Accessories": "https://www.snapdeal.com/search?keyword=accessories",
    "Footwear": "https://www.snapdeal.com/search?keyword=footwear",
    "Men Clothing": "https://www.snapdeal.com/search?keyword=men%20clothing",
    "Women Clothing": "https://www.snapdeal.com/search?keyword=women%20clothing",
}
# ==================================================

# ---------- Chrome setup ----------
chrome_opts = Options()
if HEADLESS:
    chrome_opts.add_argument("--headless=new")

chrome_opts.add_argument("--disable-gpu")
chrome_opts.add_argument("--window-size=1920,1080")
chrome_opts.add_argument("--no-sandbox")
chrome_opts.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_opts
)

wait = WebDriverWait(driver, WAIT_TIME)

# ---------- Helper ----------
def clean_rating(style):
    if not style:
        return ""
    match = re.search(r"(\d+)%", style)
    if match:
        return round(int(match.group(1)) / 20, 1)
    return ""

# ===================== MAIN =====================
all_rows = []

for section, url in BASE_SECTIONS.items():
    print(f"\nScraping Section: {section}")
    driver.get(url)

    wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.product-tuple-listing"))
    )

    cards = driver.find_elements(By.CSS_SELECTOR, "div.product-tuple-listing")

    for card in cards[:MAX_PRODUCTS]:
        try:
            name = card.find_element(By.CSS_SELECTOR, "p.product-title").text.strip()
        except:
            name = ""

        try:
            price = card.find_element(By.CSS_SELECTOR, "span.product-price").text.strip()
        except:
            price = ""

        try:
            rating_style = card.find_element(By.CSS_SELECTOR, ".filled-stars").get_attribute("style")
            rating = clean_rating(rating_style)
        except:
            rating = ""

        try:
            img = card.find_element(By.TAG_NAME, "img").get_attribute("src") or \
                  card.find_element(By.TAG_NAME, "img").get_attribute("data-src")
        except:
            img = ""

        try:
            product_url = card.find_element(By.TAG_NAME, "a").get_attribute("href")
        except:
            product_url = ""

        all_rows.append({
            "Scraped At": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Section": section,
            "Product Name": name,
            "Price": price,
            "Rating": rating,
            "Image URL": img,
            "Product URL": product_url
        })

# ---------- Save CSV ----------
df = pd.DataFrame(all_rows)
df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

print(f"\n✅ DONE! Output saved as {OUTPUT_CSV}")
driver.quit()
df.to_csv("snapdeal_products.csv",index=False)
print("csv filed saved succesfully")