import time
import re
from datetime import datetime
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service


# ================= CONFIG =================
OUTPUT_CSV = "snapdeal_products.csv"
HEADLESS = False
WAIT_TIME = 25
MAX_PRODUCTS = 10

BASE_SECTIONS = {
    "Accessories": "https://www.snapdeal.com/search?keyword=accessories",
    "Footwear": "https://www.snapdeal.com/search?keyword=footwear",
    "Men Clothing": "https://www.snapdeal.com/search?keyword=men%20clothing",
    "Women Clothing": "https://www.snapdeal.com/search?keyword=women%20clothing",
}
# ==========================================


# ---------- CHROME SETUP ----------
options = Options()
if HEADLESS:
    options.add_argument("--headless=new")

options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, WAIT_TIME)


# ---------- HELPERS ----------
def sleep(sec=2):
    time.sleep(sec)


def rating_from_style(style):
    try:
        m = re.search(r"(\d+)\s*%", style)
        if not m:
            return ""
        pct = int(m.group(1))
        return round(pct / 20, 1)
    except:
        return ""


def wait_for_cards():
    """Wait until product cards are present"""
    selectors = [
        "div.product-tuple-listing",
        "div.product-tuple"
    ]
    for sel in selectors:
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
            return sel
        except:
            continue
    return None


# ---------- SCRAPER ----------
def scrape_products(section):
    data = []

    card_selector = wait_for_cards()
    if not card_selector:
        print("⚠ No products found / blocked")
        return data

    cards = driver.find_elements(By.CSS_SELECTOR, card_selector)

    for card in cards[:MAX_PRODUCTS]:
        try:
            name = card.find_element(By.CSS_SELECTOR, "p.product-title").text.strip()
        except:
            name = ""

        try:
            price = card.find_element(By.CSS_SELECTOR, "span.product-price").text.strip()
        except:
            price = ""

        # rating
        rating = ""
        try:
            style = card.find_element(By.CSS_SELECTOR, ".filled-stars").get_attribute("style")
            rating = rating_from_style(style)
        except:
            rating = ""

        # image (lazy load safe)
        img = ""
        try:
            img_el = card.find_element(By.TAG_NAME, "img")
            img = img_el.get_attribute("src") or img_el.get_attribute("data-src") or ""
        except:
            img = ""

        # product URL
        url = ""
        try:
            url = card.find_element(By.CSS_SELECTOR, "a.dp-widget-link").get_attribute("href")
        except:
            try:
                url = card.find_element(By.TAG_NAME, "a").get_attribute("href")
            except:
                url = ""

        data.append({
            "Scraped At": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Section": section,
            "Product Name": name,
            "Price": price,
            "Rating": rating,
            "Image URL": img,
            "Product URL": url
        })

    return data


# ================= MAIN =================
all_data = []

for section, url in BASE_SECTIONS.items():
    print(f"\n🔍 Scraping: {section}")
    driver.get(url)
    sleep(4)

    products = scrape_products(section)
    print(f"✅ Collected: {len(products)} products")

    all_data.extend(products)

driver.quit()


# ---------- SAVE ----------
df = pd.DataFrame(all_data)

if df.empty:
    print("\n❌ No data scraped! (Captcha/block அல்லது selectors mismatch)")
else:
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print("\n✅ SUCCESS! File saved:", OUTPUT_CSV)
    print(df.head(5))
