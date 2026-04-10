from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import os, time

options = webdriver.ChromeOptions()
options.add_argument("--window-size=1280,900")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
profile_dir = os.path.abspath("chrome_profile")
options.add_argument(f"--user-data-dir={profile_dir}")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

driver.get("https://www.dice.com/job-detail/c45a1e0a-a7bd-4960-a847-31d2a32d598b")
time.sleep(6)

print("\n=== ALL VISIBLE BUTTONS AND LINKS ===")
buttons = driver.find_elements(By.TAG_NAME, "button")
for i, btn in enumerate(buttons):
    if btn.is_displayed():
        print(f"BUTTON [{i}] text='{btn.text.strip()}' class='{(btn.get_attribute('class') or '')[:60]}'")

links = driver.find_elements(By.TAG_NAME, "a")
for i, a in enumerate(links):
    if a.is_displayed() and a.text.strip() in ["Apply", "Easy Apply", "Apply Now"]:
        print(f"LINK [{i}] text='{a.text.strip()}' href='{a.get_attribute('href')}' class='{(a.get_attribute('class') or '')[:60]}'")

input("\nPress Enter to close...")
driver.quit()