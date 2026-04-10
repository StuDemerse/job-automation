"""
job_agent.py — Uses Selenium to log into Jobright.ai and scrape
your personalized recommended jobs. 

First run: Chrome opens and lets you log in manually.
After that: Your session is saved and it runs fully automatically.
"""

import time
import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from config import (
    MINIMUM_SALARY,
    TARGET_SALARY,
    RELEVANCE_BOOST_KEYWORDS,
    RELEVANCE_PENALTY_KEYWORDS,
)
from scraper_dice import run_dice_scraper

# ── Constants ─────────────────────────────────────────────────────────────────

JOBRIGHT_URL   = "https://jobright.ai/jobs/recommend"
SESSION_FILE   = "jobright_session.json"   # Saved cookies so you stay logged in
PAGE_LOAD_WAIT = 8    # Seconds to wait for page to load
SCROLL_PAUSES  = 8    # How many times to scroll down to load more jobs


# ── Relevance scoring (unchanged from before) ─────────────────────────────────

def parse_salary(text: str) -> tuple:
    import re
    if not text:
        return (0, 0)
    text = text.replace(",", "").lower()
    nums = re.findall(r'\$?(\d+\.?\d*)\s*k?', text)
    values = []
    for n in nums:
        val = float(n)
        if val < 1000:
            val *= 1000
        values.append(int(val))
    if len(values) >= 2:
        return (min(values), max(values))
    elif len(values) == 1:
        return (values[0], values[0])
    return (0, 0)


def score_job(job: dict) -> float:
    text = (
        job.get("title", "") + " " +
        job.get("description", "") + " " +
        job.get("company", "") + " " +
        job.get("location", "")
    ).lower()

    score = 50.0

    for kw in RELEVANCE_BOOST_KEYWORDS:
        if kw.lower() in text:
            score += 4

    for kw in RELEVANCE_PENALTY_KEYWORDS:
        if kw.lower() in text:
            score -= 8

    # Remote-only filter — penalize anything on-site or hybrid
    if "remote" in text:
        score += 15
    if any(x in text for x in ["on-site", "onsite", "on site", "hybrid"]):
        score -= 25

    sal_min, sal_max = parse_salary(job.get("salary", ""))
    if sal_max > 0:
        if sal_min >= MINIMUM_SALARY:
            score += 15
        elif sal_max >= MINIMUM_SALARY:
            score += 7
        else:
            score -= 10
        if sal_min >= TARGET_SALARY:
            score += 10

    return max(0, min(100, score))


# ── Browser setup ─────────────────────────────────────────────────────────────

def create_driver():
    """Launch Chrome looking as close to a real browser as possible."""
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1280,900")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    profile_dir = os.path.abspath("chrome_profile")
    options.add_argument(f"--user-data-dir={profile_dir}")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def is_logged_in(driver) -> bool:
    """Check if we're already logged into Jobright."""
    return "jobright.ai/jobs" in driver.current_url and "login" not in driver.current_url


def ensure_logged_in(driver):
    """
    Navigate to Jobright. If not logged in, wait for the user to do it manually.
    After first login, the Chrome profile saves the session automatically.
    """
    print("  Opening Jobright.ai...")
    driver.get(JOBRIGHT_URL)
    time.sleep(3)

    if is_logged_in(driver):
        print("  ✅ Already logged in!")
        return

    print("\n" + "="*55)
    print("  ACTION REQUIRED:")
    print("  Chrome has opened Jobright.ai.")
    print("  Please log in with your Google account in the")
    print("  browser window that just appeared.")
    print("  The script will continue automatically once")
    print("  you are logged in.")
    print("="*55 + "\n")

    # Wait up to 3 minutes for the user to log in
    for _ in range(180):
        time.sleep(1)
        if is_logged_in(driver):
            print("  ✅ Login detected! Continuing...")
            time.sleep(3)
            return

    raise TimeoutError("Login not detected after 3 minutes. Please try again.")


# ── Scraper ───────────────────────────────────────────────────────────────────

def scrape_jobs(driver) -> list:
    """Scrape job cards from the recommendations page."""
    print("  Scrolling to load all jobs...")

    jobs = []
    wait = WebDriverWait(driver, 15)

    # Scroll down to trigger lazy-loading of job cards
    for i in range(SCROLL_PAUSES):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    # Jobright.ai uses virtualized list - cards have class containing 'job-card'
    cards = driver.find_elements(By.CSS_SELECTOR, "div.job-card-flag-classname")

    if not cards:
        print(f"  ⚠️  Could not find job cards. Saving page for inspection...")
        with open("debug_selenium.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("  Saved debug_selenium.html — let Claude know!")
        return []

    for card in cards:
        try:
            title = ""
            company = ""
            salary = ""
            location = ""
            link = ""

            try:
                title = card.find_element(By.CSS_SELECTOR, "h2.ant-typography").text.strip()
            except: pass

            try:
                company = card.find_element(By.CSS_SELECTOR, "div[class*='company-name']").text.strip()
            except: pass

            try:
                money_items = card.find_elements(By.CSS_SELECTOR, "div[class*='job-metadata-item']")
                for item in money_items:
                    text = item.text.strip()
                    if "$" in text or "K/yr" in text:
                        salary = text
                        break
            except: pass

            try:
                location_els = card.find_elements(By.CSS_SELECTOR, "div[class*='job-metadata-item'] span.ant-typography")
                location = location_els[0].text.strip() if location_els else ""
            except: pass

            try:
                link_el = card.find_element(By.CSS_SELECTOR, "a[href*='/jobs/info/']")
                link = link_el.get_attribute("href") or ""
            except: pass

            if not title:
                continue

            jobs.append({
                "title": title,
                "company": company,
                "salary": salary,
                "location": location,
                "description": "",
                "link": link,
            })

        except Exception as e:
            continue

    return jobs


# ── Main agent function ───────────────────────────────────────────────────────

def run_job_agent() -> list:
    """
    Full job agent run. Returns scored and ranked job list.
    """
    print(f"\n🔍 Starting Job Agent (Jobright.ai)...")

    driver = create_driver()

    try:
        ensure_logged_in(driver)

        # Navigate to recommendations page
        driver.get(JOBRIGHT_URL)
        time.sleep(PAGE_LOAD_WAIT)

        raw_jobs = scrape_jobs(driver)
        print(f"  Scraped {len(raw_jobs)} raw listings")

    finally:
        driver.quit()
    
# Run Dice scraper
    print("\n🎲 Running Dice scraper...")
    dice_jobs = run_dice_scraper()
    raw_jobs = raw_jobs + dice_jobs
    print(f"  Combined total: {len(raw_jobs)} jobs")

    if not raw_jobs:
        return []

    # Score and sort
    for job in raw_jobs:
        job["score"] = score_job(job)
        sal_min, sal_max = parse_salary(job.get("salary", ""))
        job["salary_min"] = sal_min
        job["salary_max"] = sal_max

    # Filter out heavy on-site penalties (score below 20 = almost certainly not remote)
    ranked = sorted(raw_jobs, key=lambda j: j["score"], reverse=True)

    print(f"  ✅ {len(ranked)} jobs ranked")
    if ranked:
        print(f"  Top result: {ranked[0]['title']} @ {ranked[0]['company']} (score: {ranked[0]['score']:.0f})")

    return ranked


# ── Standalone run ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    jobs = run_job_agent()
    print(f"\n🏆 Top 10 Jobs:")
    for i, job in enumerate(jobs[:10], 1):
        salary = job.get("salary") or "Salary not listed"
        print(f"  {i:2}. [{job['score']:.0f}] {job['title']} — {job['company']}")
        print(f"       💰 {salary}  📍 {job.get('location', 'N/A')}")
        print(f"       🔗 {job.get('link', '#')}\n")