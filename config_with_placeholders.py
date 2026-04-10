"""
config.py — Central configuration for Email & Job Search Agents
Edit this file with your credentials and preferences before running.
"""

# ─────────────────────────────────────────────
# EMAIL SETTINGS
# ─────────────────────────────────────────────

YAHOO_EMAIL = "YAHOO@PLACEHOLDER.COM"
YAHOO_APP_PASSWORD = "PLACEHOLDER"   # Yahoo App Password (not your login password)
# Generate at: https://login.yahoo.com/account/security → App Passwords

GMAIL_EMAIL = "GMAIL@PLACEHOLDER.COM"
GMAIL_APP_PASSWORD = "PLACEHOLDER"   # Gmail App Password (not your login password)
# Generate at: myaccount.google.com → Security → 2-Step Verification → App Passwords

# How many days back to scan for emails (keep low for daily runs)
EMAIL_LOOKBACK_DAYS = 1

# ─────────────────────────────────────────────
# EMAIL SORTING RULES
# Each rule: {"keywords": [...], "folder": "FolderName", "priority": 1-5}
# Priority 1 = highest importance (will appear in daily digest)
# ─────────────────────────────────────────────

SORTING_RULES = [
    {
        "keywords": ["job", "opportunity", "recruiter", "hiring", "position", "role", "offer"],
        "folder": "Jobs",
        "priority": 1
    },
    {
        "keywords": ["invoice", "payment", "receipt", "billing", "charge", "transaction"],
        "folder": "Finance",
        "priority": 2
    },
    {
        "keywords": ["urgent", "action required", "important", "deadline", "expires", "asap"],
        "folder": "Urgent",
        "priority": 1
    },
    {
        "keywords": ["newsletter", "unsubscribe", "weekly digest", "monthly update", "promotion"],
        "folder": "Newsletters",
        "priority": 5
    },
    {
        "keywords": ["amazon", "order", "shipped", "delivered", "tracking"],
        "folder": "Shopping",
        "priority": 4
    },
    {
        "keywords": ["github", "gitlab", "pull request", "merge", "commit", "CI/CD", "pipeline"],
        "folder": "Dev",
        "priority": 2
    },
]

# Emails with priority <= this value will appear in the daily digest
DIGEST_PRIORITY_THRESHOLD = 2

# ─────────────────────────────────────────────
# JOB SEARCH SETTINGS
# ─────────────────────────────────────────────

JOB_SEARCH_QUERIES = [
    "AI prompt engineer",
    "LLM trainer",
    "AI support engineer",
    "technical support AI",
    "escalation engineer AI",
    "AI operations engineer",
    "automation engineer Python",
    "AI solutions engineer",
    "customer success AI engineer",
    "RLHF trainer",
    "AI implementation specialist",
    "technical account manager AI",
]

DICE_SEARCH_QUERIES = [
    "technical support",
    "escalation engineer",
    "support engineer",
    "IT support",
    "cloud support",
    "SaaS support",
    "solutions engineer",
    "systems engineer",
]

MINIMUM_SALARY = 100_000   # Jobs below this are flagged, not excluded (some don't list salary)
TARGET_SALARY  = 120_000   # Your sweet spot

# Keywords that boost a job's relevance score
RELEVANCE_BOOST_KEYWORDS = [
    "python", "ai", "llm", "machine learning", "automation", "langchain",
    "openai", "anthropic", "nlp", "data", "api", "remote", "artificial intelligence"
]

# Keywords that reduce a job's relevance score
RELEVANCE_PENALTY_KEYWORDS = [
    "10+ years", "15 years", "clearance required", "on-site only", "unpaid"
]

# ─────────────────────────────────────────────
# ANTHROPIC API (for AI-powered summaries)
# ─────────────────────────────────────────────

ANTHROPIC_API_KEY = "sk-ant-..."  # Get at console.anthropic.com
USE_AI_SUMMARIES = False           # Set False to skip AI summaries (saves API calls)

# ─────────────────────────────────────────────
# OUTPUT SETTINGS
# ─────────────────────────────────────────────

REPORT_OUTPUT_DIR = "./reports"    # Where daily reports are saved
REPORT_FORMAT = "html"             # "html" or "txt"
