"""
scraper_dice.py — Scrapes Dice.com for remote tech jobs matching
your background and salary targets.

No login required — Dice allows public job searching.
Uses Selenium to handle dynamic content loading.
"""

import os
import time
import re
import hashlib
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from config import (
    MINIMUM_SALARY,
    TARGET_SALARY,
    RELEVANCE_BOOST_KEYWORDS,
    RELEVANCE_PENALTY_KEYWORDS,
    DICE_SEARCH_QUERIES,
)

# ── Constants ─────────────────────────────────────────────────────────────────

DICE_BASE_URL = "https://www.dice.com/jobs"
PAGE_LOAD_WAIT = 8
SCROLL_PAUSES  = 3
REQUEST_DELAY  = 2


# ── Salary parsing ────────────────────────────────────────────────────────────

def parse_salary_dice(text: str) -> tuple:
    if not text:
        return (0, 0)
    text = text.replace(",", "").lower()
    # Handle "per annum", "per hour" etc
    is_hourly = "hour" in text or "/hr" in text
    nums = re.findall(r'\$?(\d+\.?\d*)\s*k?', text)
    values = []
    for n in nums:
        val = float(n)
        if val < 1000:
            val *= 1000
        if is_hourly:
            val = val * 2080  # Convert hourly to annual
        values.append(int(val))
    if len(values) >= 2:
        return (min(values), max(values))
    elif len(values) == 1:
        return (values[0], values[0])
    return (0, 0)


# ── Relevance scoring ─────────────────────────────────────────────────────────

def score_job_dice(job: dict) -> float:
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

    # Remote bonus
    if "remote" in text:
        score += 15
    if any(x in text for x in ["on-site", "onsite", "on site", "hybrid"]):
        score -= 25

    # Salary scoring
    sal_min, sal_max = parse_salary_dice(job.get("salary", ""))
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
    """Launch Chrome using main saved session."""
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1280,900")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    profile_dir = os.path.abspath("chrome_profile")
    options.add_argument(f"--user-data-dir={profile_dir}")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver

# ── Banner/popup dismissal ────────────────────────────────────────────────────

def dismiss_banners(driver):
    """Dismiss cookie banners and signup popups on Dice."""
    dismissals = [
        "//button[contains(text(), 'Dismiss')]",
        "//button[contains(text(), 'Accept')]",
        "//button[contains(text(), 'No thanks')]",
        "//button[contains(text(), 'Close')]",
        "[data-cy='dismiss-button']",
        ".close-button",
    ]
    for sel in dismissals:
        try:
            if sel.startswith("//"):
                btn = driver.find_element(By.XPATH, sel)
            else:
                btn = driver.find_element(By.CSS_SELECTOR, sel)
            if btn and btn.is_displayed():
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(0.5)
        except:
            continue


# ── Scraper ───────────────────────────────────────────────────────────────────

def scrape_dice_query(driver, query: str) -> list:
    """Scrape Dice for a single search query using Selenium."""
    url = f"https://www.dice.com/jobs?q={query.replace(' ', '+')}&pageSize=20"
    jobs = []

    print(f"  🎲 Dice: '{query}'")

    try:
        driver.get(url)
        time.sleep(8)
        dismiss_banners(driver)

        page_source = driver.page_source

        if not hasattr(scrape_dice_query, '_saved'):
            with open("debug_dice.html", "w", encoding="utf-8") as f:
                f.write(page_source)
            print(f"    💾 Saved debug_dice.html")
            scrape_dice_query._saved = True

        if 'detailsPageUrl' not in page_source:
            print(f"    ⚠️  Job data not found in page — waiting longer...")
            time.sleep(5)
            page_source = driver.page_source

        links = re.findall(r'"detailsPageUrl":"(https?://(?:www\.)?dice\.com/job-detail/[^"]+)"', page_source)
        # Also try without protocol
        if not links:
            raw_links = re.findall(r'dice\.com/job-detail/([^"\\]+)', page_source)
            links = [f"https://www.dice.com/job-detail/{l}" for l in raw_links]
        # Extract from HTML attributes
        raw_titles = re.findall(r'aria-label="View Details for ([^"]+)"', page_source)
        # Strip the guid from titles like "Job Title (abc123def456...)"
        titles = [re.sub(r'\s*\([a-f0-9]{32}\)\s*$', '', t).strip() for t in raw_titles]
        links = re.findall(r'href="(https://www\.dice\.com/job-detail/[^"]+)"[^>]*class="absolute', page_source)
        companies = re.findall(r'aria-label="Company Logo"[^>]*href="/company-profile/[^"]*companyname=([^"]+)"', page_source)
        salaries = re.findall(r'id="salary-label"[^>]*><p[^>]*>([^<]+)</p>', page_source)
        locations = re.findall(r'<p class="text-sm font-normal text-zinc-600">([^<]+)</p>', page_source)

        # Clean up company names (URL encoded)
        import urllib.parse
        companies = [urllib.parse.unquote_plus(c) for c in companies]

        print(f"    Found {len(links)} links, {len(titles)} titles, {len(companies)} companies")

        for i in range(min(len(links), len(titles), len(companies))):
            salary = salaries[i] if i < len(salaries) else ""
            location = locations[i*2] if i*2 < len(locations) else ""

            jobs.append({
                "title":       titles[i],
                "company":     companies[i],
                "salary":      salary,
                "location":    location,
                "description": "",
                "link":        links[i],
                "source":      "Dice",
                "query":       query,
                "is_remote":   "remote" in location.lower(),
            })

    except Exception as e:
        print(f"    ⚠️  Error scraping Dice for '{query}': {e}")

    print(f"    → {len(jobs)} jobs found")
    return jobs

# ── Deduplication ─────────────────────────────────────────────────────────────

def deduplicate(jobs: list) -> list:
    seen = set()
    unique = []
    for job in jobs:
        key = hashlib.md5(
            f"{job['title'].lower()}{job['company'].lower()}".encode()
        ).hexdigest()
        if key not in seen:
            seen.add(key)
            unique.append(job)
    return unique


# ── Main function ─────────────────────────────────────────────────────────────

def run_dice_scraper() -> list:
    print(f"\n🎲 Starting Dice Scraper ({len(DICE_SEARCH_QUERIES)} queries)...")
    driver = create_driver()
    all_jobs = []

    try:
        for query in DICE_SEARCH_QUERIES:
            results = scrape_dice_query(driver, query)
            all_jobs.extend(results)
            time.sleep(REQUEST_DELAY)
    finally:
        driver.quit()

    unique = deduplicate(all_jobs)
    print(f"\n  Deduped: {len(all_jobs)} → {len(unique)} unique Dice listings")

    for job in unique:
        job["score"] = score_job_dice(job)
        sal_min, sal_max = parse_salary_dice(job.get("salary", ""))
        job["salary_min"] = sal_min
        job["salary_max"] = sal_max

    ranked = sorted(unique, key=lambda j: j["score"], reverse=True)

    if ranked:
        print(f"  Top Dice result: {ranked[0]['title']} @ {ranked[0]['company']} (score: {ranked[0]['score']:.0f})")

    return ranked

# ── Standalone test ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    jobs = run_dice_scraper()
    print(f"\n🏆 Top 10 Dice Jobs:")
    for i, job in enumerate(jobs[:10], 1):
        salary = job.get("salary") or "Salary not listed"
        print(f"  {i:2}. [{job['score']:.0f}] {job['title']} — {job['company']}")
        print(f"       💰 {salary}  📍 {job.get('location', 'N/A')}")
        print(f"       🔗 {job.get('link', '#')}\n")