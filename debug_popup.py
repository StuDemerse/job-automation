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

driver.get("https://jobright.ai/jobs/info/69d4794b891d7b11cfcfac10")
time.sleep(6)

print("\n=== ALL BUTTONS ON PAGE ===")
buttons = driver.find_elements(By.TAG_NAME, "button")
for i, btn in enumerate(buttons):
    text = btn.text.strip()
    visible = btn.is_displayed()
    classes = (btn.get_attribute("class") or "")[:60]
    if visible:
        print(f"[{i}] text='{text}' | class='{classes}'")

input("\nPress Enter to close browser...")
driver.quit()