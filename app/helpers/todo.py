import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
import random

def get_price_kaina24(item_code: str, driver) -> str:
    url = f"https://www.kaina24.lt/search?q={item_code}"
    driver.get(url)

    # Wait for body to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
    )

    soup = BeautifulSoup(driver.page_source, "html.parser")
    price_a = soup.select_one("a:has(span.prefix)")
    if price_a:
        return price_a.get_text(strip=True).replace("nuo", "").strip()
    fallback_price = soup.select_one("p.price > a")
    if fallback_price:
        return fallback_price.get_text(strip=True)
    return "N/A"


def get_prices_kaina24(codes: list) -> list:
    options = uc.ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    driver = uc.Chrome(options=options)
    result = []

    try:
        # Handle consent once
        driver.get("https://www.kaina24.lt/")
        try:
            consent_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"))
            )
            consent_btn.click()
            time.sleep(1)
        except:
            pass

        # Fetch prices
        for code in codes:
            price = get_price_kaina24(code, driver)
            time.sleep(random.uniform(10, 20))
            result.append(price)

    finally:
        driver.quit()

    return result

# li = [
#     "4CHR3",
#     "BASICR4",
#     "SONOFF+Waterproof+Box(IP66)",
#     "D1",
#     "DUALR3",
#     "DUALR3-LITE",
#     "DW2-WIFI",
# ]

# print(get_prices_kaina24(li))