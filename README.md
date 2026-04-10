# Job Hunting Automation Suite

A fully automated job hunting pipeline built in Python. Runs every morning at 7AM via Windows Task Scheduler — scraping jobs from multiple boards, sorting email, scoring opportunities against salary targets, and surfacing everything through a local browser UI for review and semi-automated applying.

---

## What It Does

**Morning pipeline (automated):**
1. Sorts incoming email from Yahoo and Gmail into folders by keyword rules
2. Scrapes job listings from Jobright.ai and Dice.com using Selenium
3. Scores and ranks every job against salary targets and role keywords
4. Combines and deduplicates results across both sources
5. Generates a daily HTML briefing report

**Review flow (manual, browser-based):**
- Open `http://localhost:8765` to approve or skip jobs
- Approved jobs are saved to a persistent queue

**Apply flow (semi-automated):**
- Opens each approved job in the browser
- Handles popup dismissal and autofill triggers automatically
- Pauses for user confirmation before submitting
- Logs every application and deduplicates by company

---

## Project Structure

```
├── config.py               # Central config — credentials, salary targets, keywords
├── run_agents.py           # Main orchestrator
├── email_agent.py          # Yahoo + Gmail IMAP sorting agent
├── job_agent.py            # Jobright.ai Selenium scraper + scoring
├── scraper_dice.py         # Dice.com Selenium scraper
├── report_generator.py     # HTML daily briefing report generator
├── approval_server.py      # Local HTTP server (localhost:8765)
├── dashboard.py            # Application tracker dashboard
├── apply_agent.py          # Semi-auto apply agent
├── morning_run.bat         # Batch file for Windows Task Scheduler
├── debug_popup.py          # Debug utility — Jobright popup inspection
├── debug_dice_apply.py     # Debug utility — Dice apply button inspection
├── approved_jobs.json      # Persistent approval queue (auto-generated)
└── applications_log.json   # Application history log (auto-generated)
```

---

## Setup

### Requirements

- Python 3.10+
- Google Chrome
- ChromeDriver (matching your Chrome version)
- The following Python packages:

```bash
pip install selenium requests
```

### Configuration

Copy `config.py` and fill in your own values:

```python
# Email credentials
YAHOO_EMAIL = "your_email@yahoo.com"
YAHOO_PASSWORD = "your_app_password"
GMAIL_EMAIL = "your_email@gmail.com"
GMAIL_PASSWORD = "your_app_password"

# Salary targets
MINIMUM_SALARY = 100_000
TARGET_SALARY = 120_000

# Output
REPORT_OUTPUT_DIR = "./reports"
MAX_CREDITS_PER_RUN = 3
USE_AI_SUMMARIES = False
```

> **Note:** Use app-specific passwords for Gmail and Yahoo, not your main account password. Both require this for IMAP access.

### Chrome Profile

The scrapers use a saved Chrome profile to stay logged into Jobright.ai and Dice.com. Set the path to your Chrome profile in `config.py` before running.

---

## Running the Pipeline

**Full morning run:**
```bash
python run_agents.py
```

**Review jobs in browser:**
```bash
python approval_server.py
# Open http://localhost:8765
```

**Apply to approved jobs:**
```bash
python apply_agent.py

# Dry run (no browser actions taken):
python apply_agent.py --dry-run
```

**Automated daily run via Task Scheduler:**
- Schedule `morning_run.bat` to run at your preferred time
- The batch file launches `run_agents.py` and generates the daily report

---

## Key Features

- **Multi-source scraping** — Jobright.ai and Dice.com (138+ jobs per run)
- **Smart scoring** — ranks jobs by salary match, title relevance, and keyword overlap
- **Deduplication** — skips jobs from companies already applied to
- **Popup handling** — auto-dismisses Jobright's Orion popup via JavaScript
- **Encoding fix** — handles Gmail `unknown-8bit` encoding edge case
- **Live approval queue** — browser UI with dynamic refresh, no page reloads needed
- **Application tracker** — dashboard with status dropdowns at `/dashboard`

---

## Pending / In Progress

- [ ] Indeed scraper (`scraper_indeed.py`)
- [ ] Source label (Jobright / Dice) on briefing report job cards
- [ ] Fix Dice location occasionally showing "Today/Yesterday" instead of city
- [ ] Dice Easy Apply button automation (requires Dice login in Chrome profile)

---

## Tech Stack

Python · Selenium WebDriver · IMAP · HTML/CSS · JSON · HTTP Server · Regex · Windows Task Scheduler · Chrome Profiles

---

*Built by [Stuart DeMerse](https://github.com/StuDemerse)*
