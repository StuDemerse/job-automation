"""
report_generator.py — Builds a clean HTML daily digest combining
email summaries and ranked job listings, with an approval queue
so you can greenlight jobs before the agent applies.
"""

import os
import datetime
import json
from config import (
    REPORT_OUTPUT_DIR,
    MINIMUM_SALARY,
)

APPROVED_JOBS_FILE = "approved_jobs.json"


# ── Approval queue helpers ────────────────────────────────────────────────────

def load_approved_jobs() -> dict:
    """Load the approved jobs tracker from disk."""
    if os.path.exists(APPROVED_JOBS_FILE):
        with open(APPROVED_JOBS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_approved_jobs(data: dict):
    """Save the approved jobs tracker to disk."""
    with open(APPROVED_JOBS_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ── HTML Report Builder ───────────────────────────────────────────────────────

def build_html_report(emails: list[dict], jobs: list[dict]) -> str:
    today = datetime.date.today().strftime("%A, %B %d, %Y")
    approved = load_approved_jobs()

    # ── Job cards with approval buttons ───────────────────────────────────────
    job_cards_html = ""
    for i, job in enumerate(jobs[:20], 1):
        salary = job.get("salary") or "Not listed"
        sal_min = job.get("salary_min", 0)
        score = job.get("score", 0)
        score_color = "#4ade80" if score >= 70 else "#fbbf24" if score >= 50 else "#f87171"
        link = job.get("link", "#")
        job_id = link.split("/")[-1] if link else f"job_{i}"

        # Check approval status
        status = approved.get(job_id, {}).get("status", "pending")
        if status == "approved":
            status_badge = '<span class="badge approved">✅ Approved</span>'
            card_class = "job-card approved-card"
        elif status == "skipped":
            status_badge = '<span class="badge skipped">❌ Skipped</span>'
            card_class = "job-card skipped-card"
        else:
            status_badge = ""
            card_class = "job-card"

        remote_badge = '<span class="badge remote">Remote</span>' if "remote" in (job.get("location","") + job.get("description","")).lower() else ""

        job_cards_html += f"""
        <div class="{card_class}" id="card_{job_id}" data-job-id="{job_id}">
          <div class="job-card-header">
            <div class="job-rank">#{i}</div>
            <div class="job-score-dot" style="background:{score_color}">{score:.0f}</div>
            <div class="job-info">
              <div class="job-title"><a href="{link}" target="_blank">{job.get('title','N/A')}</a></div>
              <div class="job-meta">{job.get('company','N/A')} &nbsp;·&nbsp; {salary} &nbsp;·&nbsp; {job.get('location','N/A')} {remote_badge}</div>
            </div>
            <div class="status-badge-wrap">{status_badge}</div>
          </div>
          <div class="job-card-actions">
            <button class="btn-approve" onclick="approveJob('{job_id}', '{job.get('title','').replace("'","").replace('"','')}', '{job.get('company','').replace("'","")}', '{salary}', '{link}')">
              ✅ Approve — Add to Apply Queue
            </button>
            <button class="btn-skip" onclick="skipJob('{job_id}')">
              ❌ Skip
            </button>
            <a href="{link}" target="_blank" class="btn-view">🔗 View Job</a>
          </div>
        </div>"""

    # ── Approved jobs summary panel ───────────────────────────────────────────
    approved_list_html = ""
    approved_jobs = [(jid, jdata) for jid, jdata in approved.items() if jdata.get("status") == "approved"]
    if approved_jobs:
        for jid, jdata in approved_jobs:
            approved_list_html += f"""
            <div class="approved-item">
              <div class="approved-item-info">
                <span class="approved-item-title">{jdata.get('title','N/A')}</span>
                <span class="approved-item-company">{jdata.get('company','N/A')}</span>
                <span class="approved-item-salary">{jdata.get('salary','')}</span>
              </div>
              <div class="approved-item-actions">
                <span class="approved-date">Added {jdata.get('date','')}</span>
                <button class="btn-remove" onclick="removeJob('{jid}')">Remove</button>
              </div>
            </div>"""
    else:
        approved_list_html = '<div class="empty-approved">No jobs approved yet — approve some from the list below!</div>'

    # ── Email rows ─────────────────────────────────────────────────────────────
    email_rows = ""
    priority_labels = {1: ("🔴", "Critical"), 2: ("🟠", "Important"), 3: ("🟡", "Normal"), 4: ("🔵", "Low"), 5: ("⚪", "FYI")}
    for e in emails:
        p = e.get("priority", 3)
        icon, label = priority_labels.get(p, ("⚪", ""))
        email_rows += f"""
        <tr>
          <td>{icon} {label}</td>
          <td class="email-folder">{e.get('folder','')}</td>
          <td>{e.get('subject','')[:70]}</td>
          <td class="email-sender">{e.get('sender','')[:40]}</td>
          <td class="email-account">{e.get('provider','').title()}</td>
        </tr>"""

    if not email_rows:
        email_rows = '<tr><td colspan="5" class="empty">No high-priority emails today 🎉</td></tr>'
    if not job_cards_html:
        job_cards_html = '<div class="empty">No jobs found today.</div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Daily Briefing — {today}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  :root {{
    --bg: #0f1117;
    --surface: #1a1d27;
    --surface2: #22263a;
    --border: #2e3350;
    --accent: #6ee7f7;
    --accent2: #a78bfa;
    --green: #4ade80;
    --yellow: #fbbf24;
    --red: #f87171;
    --text: #e2e8f0;
    --muted: #64748b;
    --mono: 'IBM Plex Mono', monospace;
    --sans: 'IBM Plex Sans', sans-serif;
  }}

  body {{
    background: var(--bg);
    color: var(--text);
    font-family: var(--sans);
    font-size: 14px;
    line-height: 1.6;
    padding: 2rem;
    max-width: 1000px;
    margin: 0 auto;
  }}

  header {{
    border-bottom: 1px solid var(--border);
    padding-bottom: 1.5rem;
    margin-bottom: 2rem;
  }}

  .header-top {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
  }}

  h1 {{
    font-family: var(--mono);
    font-size: 1.4rem;
    color: var(--accent);
  }}

  .date-tag {{
    font-family: var(--mono);
    font-size: 0.75rem;
    color: var(--muted);
    background: var(--surface);
    border: 1px solid var(--border);
    padding: 0.3rem 0.7rem;
    border-radius: 4px;
  }}

  section {{ margin-bottom: 2.5rem; }}

  h2 {{
    font-family: var(--mono);
    font-size: 0.8rem;
    letter-spacing: 0.12em;
    color: var(--muted);
    text-transform: uppercase;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }}

  h2 .count {{
    background: var(--surface2);
    border: 1px solid var(--border);
    color: var(--accent);
    font-size: 0.7rem;
    padding: 0.1rem 0.5rem;
    border-radius: 20px;
  }}

  /* ── Job Cards ── */
  .job-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
    transition: border-color 0.2s;
  }}

  .job-card:hover {{ border-color: var(--accent); }}

  .approved-card {{
    border-color: #166534;
    background: #0f2318;
  }}

  .skipped-card {{
    opacity: 0.45;
    border-color: var(--border);
  }}

  .job-card-header {{
    display: flex;
    align-items: center;
    gap: 0.8rem;
    margin-bottom: 0.8rem;
  }}

  .job-rank {{
    font-family: var(--mono);
    color: var(--muted);
    font-size: 0.75rem;
    min-width: 24px;
  }}

  .job-score-dot {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    font-family: var(--mono);
    font-size: 0.7rem;
    font-weight: 600;
    color: #0f1117;
    flex-shrink: 0;
  }}

  .job-info {{ flex: 1; min-width: 0; }}

  .job-title a {{
    color: var(--text);
    text-decoration: none;
    font-weight: 600;
    font-size: 0.95rem;
  }}

  .job-title a:hover {{ color: var(--accent); }}

  .job-meta {{
    color: var(--muted);
    font-size: 0.8rem;
    margin-top: 0.2rem;
  }}

  .status-badge-wrap {{ flex-shrink: 0; }}

  .job-card-actions {{
    display: flex;
    gap: 0.6rem;
    flex-wrap: wrap;
  }}

  .btn-approve {{
    background: #166534;
    color: #4ade80;
    border: 1px solid #166534;
    padding: 0.4rem 0.9rem;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.8rem;
    font-family: var(--sans);
    transition: background 0.15s;
  }}

  .btn-approve:hover {{ background: #15803d; }}

  .btn-skip {{
    background: transparent;
    color: var(--red);
    border: 1px solid #7f1d1d;
    padding: 0.4rem 0.9rem;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.8rem;
    font-family: var(--sans);
    transition: background 0.15s;
  }}

  .btn-skip:hover {{ background: #7f1d1d22; }}

  .btn-view {{
    background: transparent;
    color: var(--accent);
    border: 1px solid var(--border);
    padding: 0.4rem 0.9rem;
    border-radius: 6px;
    font-size: 0.8rem;
    text-decoration: none;
    transition: border-color 0.15s;
  }}

  .btn-view:hover {{ border-color: var(--accent); }}

  .btn-remove {{
    background: transparent;
    color: var(--muted);
    border: 1px solid var(--border);
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.72rem;
    font-family: var(--sans);
  }}

  /* ── Badges ── */
  .badge {{
    display: inline-block;
    font-size: 0.65rem;
    font-family: var(--mono);
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    margin-left: 0.4rem;
    vertical-align: middle;
  }}

  .badge.remote {{ background: #064e3b; color: #6ee7b7; border: 1px solid #065f46; }}
  .badge.approved {{ background: #166534; color: #4ade80; border: 1px solid #15803d; }}
  .badge.skipped {{ background: #1c1917; color: var(--muted); border: 1px solid var(--border); }}

  /* ── Approved Queue Panel ── */
  .approved-panel {{
    background: #0f2318;
    border: 1px solid #166534;
    border-radius: 10px;
    padding: 1.2rem;
    margin-bottom: 2rem;
  }}

  .approved-item {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.6rem 0;
    border-bottom: 1px solid #166534;
    gap: 1rem;
  }}

  .approved-item:last-child {{ border-bottom: none; }}

  .approved-item-info {{ display: flex; gap: 1rem; align-items: center; flex-wrap: wrap; }}

  .approved-item-title {{ font-weight: 600; font-size: 0.85rem; }}

  .approved-item-company {{ color: var(--muted); font-size: 0.8rem; }}

  .approved-item-salary {{ color: var(--green); font-family: var(--mono); font-size: 0.75rem; }}

  .approved-item-actions {{ display: flex; gap: 0.8rem; align-items: center; flex-shrink: 0; }}

  .approved-date {{ font-family: var(--mono); font-size: 0.65rem; color: var(--muted); }}

  .empty-approved {{ color: var(--muted); font-style: italic; font-size: 0.85rem; }}

  /* ── Email Table ── */
  table {{
    width: 100%;
    border-collapse: collapse;
    background: var(--surface);
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid var(--border);
  }}

  thead th {{
    background: var(--surface2);
    padding: 0.7rem 1rem;
    text-align: left;
    font-family: var(--mono);
    font-size: 0.65rem;
    letter-spacing: 0.08em;
    color: var(--muted);
    text-transform: uppercase;
    border-bottom: 1px solid var(--border);
  }}

  tbody tr {{ border-bottom: 1px solid var(--border); transition: background 0.15s; }}
  tbody tr:last-child {{ border-bottom: none; }}
  tbody tr:hover {{ background: var(--surface2); }}

  td {{ padding: 0.75rem 1rem; vertical-align: middle; }}

  .email-folder {{ font-family: var(--mono); font-size: 0.75rem; color: var(--accent2); }}
  .email-sender {{ color: var(--muted); font-size: 0.8rem; }}
  .email-account {{ font-family: var(--mono); font-size: 0.7rem; color: var(--muted); }}

  .empty {{ color: var(--muted); text-align: center; padding: 2rem; font-style: italic; }}

  footer {{
    text-align: center;
    font-family: var(--mono);
    font-size: 0.65rem;
    color: var(--muted);
    margin-top: 3rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border);
  }}

  #toast {{
    position: fixed;
    bottom: 2rem;
    right: 2rem;
    background: #166534;
    color: #4ade80;
    padding: 0.8rem 1.4rem;
    border-radius: 8px;
    font-family: var(--mono);
    font-size: 0.8rem;
    display: none;
    z-index: 999;
    border: 1px solid #15803d;
  }}
</style>
</head>
<body>

<header>
  <div class="header-top">
    <h1>⚡ Daily Briefing</h1>
    <span class="date-tag">{today}</span>
  </div>
</header>

<!-- ── Approved Jobs Queue ── -->
<section>
  <h2>🎯 Apply Queue <span class="count">{len(approved_jobs)} approved</span></h2>
  <div class="approved-panel">
    {approved_list_html}
  </div>
</section>

<!-- ── Job Listings with Approve/Skip ── -->
<section>
  <h2>💼 Today's Matches <span class="count">{len(jobs)} found</span></h2>
  {job_cards_html}
</section>

<!-- ── Important Emails ── -->
<section>
  <h2>📬 Important Emails <span class="count">{len(emails)} flagged</span></h2>
  <table>
    <thead>
      <tr>
        <th>Priority</th>
        <th>Folder</th>
        <th>Subject</th>
        <th>From</th>
        <th>Account</th>
      </tr>
    </thead>
    <tbody>
      {email_rows}
    </tbody>
  </table>
</section>

<footer>Generated by your Personal Automation Agent • {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}</footer>

<div id="toast"></div>

<script>
  function showToast(msg, color) {{
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.style.background = color === 'red' ? '#7f1d1d' : '#166534';
    t.style.color = color === 'red' ? '#f87171' : '#4ade80';
    t.style.borderColor = color === 'red' ? '#991b1b' : '#15803d';
    t.style.display = 'block';
    setTimeout(() => t.style.display = 'none', 2500);
  }}

  function approveJob(jobId, title, company, salary, link) {{
    fetch('http://localhost:8765/approve', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{jobId: jobId, title: title, company: company, salary: salary, link: link, status: 'approved', date: new Date().toLocaleDateString()}})
    }}).then(r => r.json()).then(data => {{
      if (data.ok) {{
        const card = document.getElementById('card_' + jobId);
        card.className = 'job-card approved-card';
        const wrap = card.querySelector('.status-badge-wrap');
        wrap.innerHTML = '<span class="badge approved">✅ Approved</span>';
        showToast('✅ Added to apply queue!', 'green');
        refreshQueue();
      }}
    }}).catch(() => {{
      showToast('✅ Approval saved!', 'green');
    }});
  }}

  function skipJob(jobId) {{
    fetch('http://localhost:8765/skip', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{jobId: jobId, status: 'skipped'}})
    }}).then(r => r.json()).then(data => {{
      if (data.ok) {{
        const card = document.getElementById('card_' + jobId);
        card.className = 'job-card skipped-card';
        showToast('❌ Job skipped', 'red');
      }}
    }}).catch(() => {{
      showToast('❌ Skipped!', 'red');
    }});
  }}

  function removeJob(jobId) {{
    fetch('http://localhost:8765/remove', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{jobId: jobId}})
    }}).then(r => r.json()).then(() => refreshQueue())
    .catch(() => refreshQueue());
  }}

  function refreshQueue() {{
    fetch('http://localhost:8765/approved-jobs')
      .then(r => r.json())
      .then(data => {{
        const panel = document.querySelector('.approved-panel');
        const countEl = document.querySelector('h2 .count');
        if (countEl) countEl.textContent = data.count + ' approved';

        if (data.count === 0) {{
          panel.innerHTML = '<div class="empty-approved">No jobs approved yet — approve some from the list below!</div>';
          return;
        }}

        let html = '';
        for (const [jid, jdata] of Object.entries(data.jobs)) {{
          html += `
          <div class="approved-item">
            <div class="approved-item-info">
              <span class="approved-item-title">${{jdata.title || 'N/A'}}</span>
              <span class="approved-item-company">${{jdata.company || 'N/A'}}</span>
              <span class="approved-item-salary">${{jdata.salary || ''}}</span>
            </div>
            <div class="approved-item-actions">
              <span class="approved-date">${{jdata.date || ''}}</span>
              <button class="btn-remove" onclick="removeJob('${{jid}}')">Remove</button>
            </div>
          </div>`;
        }}
        panel.innerHTML = html;
      }})
      .catch(err => console.log('Queue refresh error:', err));
  }}

  refreshQueue();
</script>
</body>
</html>"""


def save_report(emails: list[dict], jobs: list[dict]) -> str:
    """Generate and save the HTML report. Returns the file path."""
    os.makedirs(REPORT_OUTPUT_DIR, exist_ok=True)
    html = build_html_report(emails, jobs)
    filename = datetime.date.today().strftime("briefing_%Y-%m-%d.html")
    path = os.path.join(REPORT_OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n📊 Report saved: {path}")
    return path


if __name__ == "__main__":
    test_emails = [{"provider": "gmail", "subject": "Exciting AI Role", "sender": "recruiter@tech.com", "date": "Today", "folder": "Jobs", "priority": 1}]
    test_jobs = [{"title": "AI Engineer", "company": "OpenAI", "salary": "$120k–$160k", "location": "Remote", "description": "llm python", "link": "https://jobright.ai/jobs/info/test123", "score": 88, "salary_min": 120000, "salary_max": 160000}]
    path = save_report(test_emails, test_jobs)
    print(f"Test report: {path}")