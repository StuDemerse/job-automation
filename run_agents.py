"""
run_agents.py — Main orchestrator. Run this every morning to:
  1. Sort your Yahoo & Gmail inboxes
  2. Search Jobrite.ai for matching roles
  3. Generate a beautiful HTML daily briefing

USAGE:
  python run_agents.py              # Full run
  python run_agents.py --email      # Email agent only
  python run_agents.py --jobs       # Job agent only
  python run_agents.py --report     # Regenerate last report only

SCHEDULING (run automatically every morning):
  Mac/Linux — add to crontab:
    0 7 * * * cd /path/to/job_email_agents && python run_agents.py

  Windows — Task Scheduler:
    Action: python C:\\path\\to\\job_email_agents\\run_agents.py
    Trigger: Daily at 7:00 AM
"""

import sys
import time
import datetime
import webbrowser
from email_agent import run_all_email_agents
from job_agent import run_job_agent
from report_generator import save_report

BANNER = """
╔══════════════════════════════════════════════╗
║      Personal Automation Agent v1.0         ║
║      Email Sorting + Job Search             ║
╚══════════════════════════════════════════════╝
"""

def run_full():
    print(BANNER)
    start = time.time()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"🕐 Starting run at {now}\n")

    # ── Step 1: Email Agent ────────────────────────────────────────────────────
    digest_emails = []
    try:
        digest_emails = run_all_email_agents()
    except Exception as e:
        print(f"❌ Email agent error: {e}")
        print("   Continuing with job search...\n")

    # ── Step 2: Job Agent ──────────────────────────────────────────────────────
    jobs = []
    try:
        jobs = run_job_agent()
    except Exception as e:
        print(f"❌ Job agent error: {e}")
        print("   Continuing with report generation...\n")

    # ── Step 3: Generate Report ────────────────────────────────────────────────
    report_path = save_report(digest_emails, jobs)

    elapsed = time.time() - start
    print(f"\n✅ Done in {elapsed:.1f}s")
    print(f"   📧 {len(digest_emails)} important email(s) flagged")
    print(f"   💼 {len(jobs)} job(s) found")
    print(f"   📄 Report: {report_path}")

    # Auto-open in browser
    try:
        webbrowser.open(f"file://{__import__('os').path.abspath(report_path)}")
        print("   🌐 Opening report in browser...")
    except Exception:
        pass

    return report_path


def run_email_only():
    print(BANNER)
    print("Running Email Agent only...\n")
    results = run_all_email_agents()
    print(f"\n📋 {len(results)} important email(s) flagged for digest")
    for e in results:
        print(f"  [{e['priority']}] {e['folder']} | {e['subject'][:55]}")


def run_jobs_only():
    print(BANNER)
    print("Running Job Agent only...\n")
    jobs = run_job_agent()
    print(f"\n🏆 Top 10 Matches:")
    for i, job in enumerate(jobs[:10], 1):
        salary = job.get("salary") or "Salary not listed"
        print(f"  {i:2}. [{job['score']:.0f}] {job['title']} — {job['company']}")
        print(f"       💰 {salary}  📍 {job.get('location', 'N/A')}")
        print(f"       🔗 {job.get('link', '#')}\n")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    args = sys.argv[1:]

    if "--email" in args:
        run_email_only()
    elif "--jobs" in args:
        run_jobs_only()
    elif "--report" in args:
        # Re-run report with empty data (useful for testing template)
        save_report([], [])
    else:
        run_full()
