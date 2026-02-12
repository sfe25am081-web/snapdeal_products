import time
import re
from datetime import datetime
from urllib.parse import urlparse
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# ===================== CONFIG =====================
OUTPUT_CSV = "snapdeal_products.csv"
HEADLESS = True
SCROLL_PAUSE = 0.8
LISTING_WAIT = 10            # seconds for listing to appear
PRODUCT_WAIT = 10            # seconds for product page
MAX_PAGES_PER_SUBCAT = 5     # pages per subcategory
DEEP_SCRAPE = True           # visit each product page for max columns
LEFT_X_THRESHOLD = 420       # px: anchors with x < this are considered in left filter panel
MAX_PRODUCTS_PER_SUBCAT = None  # None for unlimited; or set e.g. 200

BASE_SECTIONS = {
    "Accessories":     "https://www.snapdeal.com/search?keyword=accessories&sort=rlvncy",
    "Footwear":        "https://www.snapdeal.com/search?keyword=footwear&sort=rlvncy",
    "Kids' Fashion":   "https://www.snapdeal.com/search?keyword=kids%20fashion&sort=rlvncy",
    "Men's Clothing":  "https://www.snapdeal.com/search?keyword=men%20clothing&sort=rlvncy",
    "Women's Clothing":"https://www.snapdeal.com/search?keyword=women%20clothing&sort=rlvncy",
}
# ==================================================


# ---------- Selenium setup ----------
chrome_opts = Options()
if HEADLESS:
    # newer headless is more stable
    chrome_opts.add_argument("--headless=new")
chrome_opts.add_argument("--disable-gpu")
chrome_opts.add_argument("--window-size=1920,1080")
chrome_opts.add_argument("--no-sandbox")
chrome_opts.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_opts
)
wait = WebDriverWait(driver, LISTING_WAIT)

def human_sleep(sec):
    time.sleep(sec)

def scroll_to_bottom():
    last = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        human_sleep(SCROLL_PAUSE)
        new = driver.execute_script("return document.body.scrollHeight")
        if new == last:
            break
        last = new

def clean_int(text: str) -> int:
    """Extract first integer from text, else 0."""
    if not text:
        return 0
    nums = re.findall(r"\d+", text)
    return int(nums[0]) if nums else 0

def parse_rating_from_style(style: str) -> str:
    """
    Some ratings are shown as stars with style='width: 86%'.
    Convert % to 0-5 scale: rating ≈ round(percent/20, 1)
    """
    if not style:
        return ""
    m = re.search(r"(\d+(?:\.\d+)?)\s*%", style)
    if not m:
        return ""
    pct = float(m.group(1))
    return f"{round(pct/20, 1)}"

def safe_text(el):
    try:
        return el.text.strip()
    except:
        return ""

def find_first(selector_list, in_el=None, attr=None, by=By.CSS_SELECTOR):
    """Try multiple selectors; return text or attribute when found."""
    ctx = in_el if in_el is not None else driver
    for sel in selector_list:
        try:
            el = ctx.find_element(by, sel)
            return el.get_attribute(attr).strip() if attr else el.text.strip()
        except:
            continue
    return ""

def find_all(selector, in_el=None, by=By.CSS_SELECTOR):
    ctx = in_el if in_el is not None else driver
    try:
        return ctx.find_elements(by, selector)
    except:
        return []

def get_left_subcategory_links():
    """
    Collect visible subcategory links from the left panel on a search page.
    We use broad selectors + coordinate filtering (x < LEFT_X_THRESHOLD).
    """
    subcats = []
    anchors = driver.find_elements(By.XPATH, "//a[@href]")
    seen = set()

    for a in anchors:
        try:
            href = a.get_attribute("href") or ""
            text = a.text.strip()
            if not text or len(text) > 60 or len(text) < 3:
                continue

            # Consider only SNAPDEAL links that look like category/search
            netloc = urlparse(href).netloc or ""
            if "snapdeal" not in netloc:
                continue
            if ("/products/" not in href) and ("/search" not in href):
                continue

            # left-panel coordinate heuristic
            loc = a.location
            if loc and isinstance(loc.get("x", None), (int, float)) and loc["x"] < LEFT_X_THRESHOLD:
                key = (text, href)
                if key in seen:
                    continue
                # filter out obvious non-category filters (price ranges, ratings stars text)
                lower = text.lower()
                if any(kw in lower for kw in [
                    "price", "brand", "rating", "size", "color", "discount",
                    "customer", "ship", "cod", "delivery", "availability", "seller",
                    "apply", "clear", "sort", "view", "more", "less", "newest",
                    "4★", "3★", "2★", "1★"
                ]):
                    continue
                # avoid purely numeric/count links
                if re.fullmatch(r"\d[\d,\. ]*", text):
                    continue

                subcats.append({"Subcategory": text, "URL": href})
                seen.add(key)
        except Exception:
            continue

    return subcats


def click_next_page():
    """Try multiple ways to go to the next page. Return True if navigated."""
    selectors = [
        "a[rel='next']",
        "a.pagination-number.next",
        "a.next",
        "//a[contains(translate(., 'NEXT', 'next'),'next')]",
    ]

    curr_url = driver.current_url
    for sel in selectors:
        try:
            if sel.startswith("//"):
                cand = driver.find_element(By.XPATH, sel)
            else:
                cand = driver.find_element(By.CSS_SELECTOR, sel)
            driver.execute_script("arguments[0].click();", cand)
            human_sleep(1.2)
            # wait for URL change or new content
            try:
                WebDriverWait(driver, 6).until(EC.url_changes(curr_url))
            except:
                pass
            if driver.current_url != curr_url:
                return True
        except:
            continue
    return False


def deep_scrape_product(url):
    """
    Open product in a new tab and extract rich details.
    Returns dict with many optional fields (empty if not found).
    """
    data = {
        "Brand": "",
        "Full Description": "",
        "Seller": "",
        "Availability": "",
        "Rating": "",
        "Reviews Count": 0,
        "Breadcrumb": "",
        "Image URLs (detail)": ""
    }
    if not url:
        return data

    parent = driver.current_window_handle
    try:
        driver.execute_script("window.open(arguments[0], '_blank');", url)
        WebDriverWait(driver, PRODUCT_WAIT).until(EC.number_of_windows_to_be(2))
        # switch to new
        for h in driver.window_handles:
            if h != parent:
                driver.switch_to.window(h)
                break

        # brand (multiple fallbacks)
        data["Brand"] = find_first([
            "span[itemprop='brand']",
            "a#brand",
            ".pdp-e-i-brand a",
            ".pdp-e-i-brand",  # sometimes plain text
        ])

        # rating (try numeric or from star width)
        rating_val = find_first([
            "span[itemprop='ratingValue']",
            ".pdp-e-i-rating",        # sometimes plain text
        ])
        if not rating_val:
            style = find_first([".filled-stars"], attr="style")
            rating_val = parse_rating_from_style(style)
        data["Rating"] = rating_val

        # reviews count
        rc_text = find_first([
            "span[itemprop='reviewCount']",
            ".pdp-review-count",
            ".product-review-count",
            ".rating-count"
        ])
        data["Reviews Count"] = clean_int(rc_text)

        # availability
        avail = find_first([
            ".sold-out-err",
            "#isCODMsg",
            ".availability-msg"
        ])
        data["Availability"] = avail or "In Stock"

        # seller
        data["Seller"] = find_first([
            "#sellerName",
            ".pdp-seller-info a",
            ".pdp-seller-info"
        ])

        # full description / specs (pick the biggest chunk)
        description_candidates = [
            "#description",
            "#productDesc",
            ".product-desc",
            ".tab-content .spec-body",
            ".spec-body",
            ".details-info",
        ]
        body = ""
        for sel in description_candidates:
            txt = find_first([sel])
            if txt and len(txt) > len(body):
                body = txt
        data["Full Description"] = body

        # breadcrumb
        crumbs = find_all("ul.breadcrumb li")
        if crumbs:
            data["Breadcrumb"] = " > ".join([safe_text(li) for li in crumbs if safe_text(li)])

        # detail images
        detail_imgs = []
        for img in find_all(".cloudzoom"):
            src = img.get_attribute("src") or img.get_attribute("data-src")
            if src:
                detail_imgs.append(src)
        if not detail_imgs:
            for img in find_all("img"):
                s = img.get_attribute("src") or ""
                if s and "snapdeal" in s and ("images" in s or "img" in s):
                    detail_imgs.append(s)
        data["Image URLs (detail)"] = ", ".join(dict.fromkeys(detail_imgs))[:2000]  # Dedup & bound

    except Exception:
        pass
    finally:
        # close tab & return
        try:
            driver.close()
            driver.switch_to.window(parent)
        except:
            pass

    return data


def scrape_listing_cards(category_name, subcat_name, page_num, max_take=None):
    """Scrape all cards on current listing page; deep-scrape each product if enabled."""
    items = []
    cards = find_all("div.product-tuple-listing")
    if not cards:
        # fallback older class
        cards = find_all("div.product-tuple")

    for idx, card in enumerate(cards, start=1):
        if max_take and len(items) >= max_take:
            break

        # Listing-level fields
        name = find_first(["p.product-title"], in_el=card) or ""
        price = find_first(["span.product-price"], in_el=card) or ""
        original_price = find_first(
            ["span.product-desc-price.strike", "span.lfloat.product-desc-price.strike"],
            in_el=card
        )
        discount = find_first(["div.product-discount", "span.product-discount"], in_el=card)
        rating_list = find_first(["p.prod-rating", ".rating"], in_el=card)
        rating_style = find_first([".filled-stars"], in_el=card, attr="style")
        if not rating_list and rating_style:
            rating_list = parse_rating_from_style(rating_style)

        rev_text = find_first(["p.product-rating-count", ".rating-count"], in_el=card)
        reviews_count = clean_int(rev_text)

        img = find_first(["img.product-image"], in_el=card, attr="src")
        if not img:
            img = find_first(["img"], in_el=card, attr="src")

        # URL: prefer dp-widget-link if present, else first <a>
        url = find_first(["a.dp-widget-link"], in_el=card, attr="href")
        if not url:
            try:
                url = card.find_element(By.TAG_NAME, "a").get_attribute("href")
            except:
                url = ""

        short_desc = find_first(["p.product-desc-rating"], in_el=card) or ""

        # audience classifier
        text_for_audience = f"{name} {short_desc}".lower()
        if any(k in text_for_audience for k in ["women", "girl", "ladies", "female"]):
            audience = "Female"
        elif any(k in text_for_audience for k in ["men", "boy", "male"]):
            audience = "Male"
        elif any(k in text_for_audience for k in ["kid", "child", "children"]):
            audience = "Children"
        else:
            audience = "Unspecified"

        # deep details
        extra = deep_scrape_product(url) if DEEP_SCRAPE and url else {
            "Brand": "",
            "Full Description": "",
            "Seller": "",
            "Availability": "",
            "Rating": "",
            "Reviews Count": 0,
            "Breadcrumb": "",
            "Image URLs (detail)": ""
        }

        # if Brand still empty, try name-leading token as heuristic
        if not extra.get("Brand"):
            extra["Brand"] = name.split()[0] if name else ""

        row = {
            "Scraped At": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Top Section": category_name,
            "Subcategory": subcat_name,
            "Product Name": name,
            "Brand (heuristic/listing)": extra.get("Brand", ""),
            "Price": price,
            "Original Price": original_price,
            "Discount": discount,
            "Rating (listing)": rating_list,
            "Rating (detail)": extra.get("Rating", ""),
            "Reviews Count (listing)": reviews_count,
            "Reviews Count (detail)": extra.get("Reviews Count", 0),
            "Target Audience": audience,
            "Availability": extra.get("Availability", ""),
            "Seller": extra.get("Seller", ""),
            "Product URL": url,
            "Image URL (listing)": img,
            "Image URLs (detail)": extra.get("Image URLs (detail)", ""),
            "Short Description": short_desc,
            "Full Description": extra.get("Full Description", ""),
            "Breadcrumb": extra.get("Breadcrumb", ""),
            "Page": page_num
        }
        items.append(row)

    return items


# ===================== MAIN =====================
all_rows = []

for section_name, base_url in BASE_SECTIONS.items():
    print(f"\n=== Section: {section_name} ===")
    driver.get(base_url)
    # wait for any product list (ensures page is settled)
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-tuple-listing")))
    except:
        pass

    # find subcategory links from left panel
    subcats = get_left_subcategory_links()
    # de-dup & keep stable order
    seen_sc = set()
    cleaned_subcats = []
    for sc in subcats:
        key = (sc["Subcategory"], sc["URL"])
        if key not in seen_sc:
            cleaned_subcats.append(sc)
            seen_sc.add(key)

    if not cleaned_subcats:
        # fallback: at least scrape the base section itself
        cleaned_subcats = [{"Subcategory": "(All)", "URL": base_url}]

    print(f"Found {len(cleaned_subcats)} subcategories")

    for sc in cleaned_subcats:
        sub_name = sc["Subcategory"]
        sub_url = sc["URL"]
        print(f"\n→ Subcategory: {sub_name}")
        driver.get(sub_url)
        # small wait for products to appear
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-tuple-listing")))
        except:
            pass

        total_this_sub = 0
        for page in range(1, MAX_PAGES_PER_SUBCAT + 1):
            print(f"   • Page {page}")
            scroll_to_bottom()
            items = scrape_listing_cards(section_name, sub_name, page,
                                         max_take=MAX_PRODUCTS_PER_SUBCAT)
            if not items:
                print("     – No products found on this page.")
                break

            all_rows.extend(items)
            total_this_sub += len(items)

            # pagination
            moved = click_next_page()
            if not moved:
                print("     – No Next button or reached last page.")
                break

        print(f"   Collected {total_this_sub} products from '{sub_name}'")

# Write CSV (even if empty, with columns)
columns = [
    "Scraped At", "Top Section", "Subcategory",
    "Product Name", "Brand (heuristic/listing)",
    "Price", "Original Price", "Discount",
    "Rating (listing)", "Rating (detail)",
    "Reviews Count (listing)", "Reviews Count (detail)",
    "Target Audience", "Availability", "Seller",
    "Product URL", "Image URL (listing)", "Image URLs (detail)",
    "Short Description", "Full Description", "Breadcrumb",
    "Page"
]
df = pd.DataFrame(all_rows, columns=columns)
df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

print(f"\n✔ Done. Rows: {len(df)}  →  {OUTPUT_CSV}")

driver.quit()
