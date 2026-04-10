"""
dashboard.py — Application tracker dashboard.
Served at http://localhost:8765/dashboard
"""

import json
import os
import datetime

APPLICATIONS_LOG = "applications_log.json"


def load_applications_log() -> list:
    if os.path.exists(APPLICATIONS_LOG):
        with open(APPLICATIONS_LOG, "r") as f:
            return json.load(f)
    return []


def build_dashboard() -> str:
    log = load_applications_log()
    today = datetime.date.today().strftime("%A, %B %d, %Y")

    # ── Stats ─────────────────────────────────────────────────────────────────
    total = len(log)
    counts = {
        "applied":             0,
        "interviewing":        0,
        "offer":               0,
        "rejected":            0,
        "withdrawn":           0,
        "skipped":             0,
        "applied-unconfirmed": 0,
        "dry-run":             0,
    }
    for entry in log:
        s = entry.get("status", "").lower()
        if s in counts:
            counts[s] += 1

    active = counts["applied"] + counts["applied-unconfirmed"] + counts["interviewing"]
    response_rate = 0
    if total > 0:
        responded = counts["interviewing"] + counts["offer"] + counts["rejected"]
        response_rate = round((responded / max(total, 1)) * 100)

    # ── Application rows ──────────────────────────────────────────────────────
    status_colors = {
        "applied":             ("#3b82f6", "Applied"),
        "applied-unconfirmed": ("#6366f1", "Applied (Unconfirmed)"),
        "interviewing":        ("#f59e0b", "Interviewing"),
        "offer":               ("#4ade80", "Offer! 🎉"),
        "rejected":            ("#f87171", "Rejected"),
        "withdrawn":           ("#94a3b8", "Withdrawn"),
        "skipped":             ("#64748b", "Skipped"),
        "dry-run":             ("#475569", "Dry Run"),
        "failed":              ("#ef4444", "Failed"),
    }

    status_options = ["applied", "interviewing", "offer", "rejected", "withdrawn"]

    rows_html = ""
    for entry in reversed(log):
        status = entry.get("status", "applied").lower()
        color, label = status_colors.get(status, ("#64748b", status.title()))
        job_id = entry.get("job_id", "")
        title = entry.get("title", "N/A")
        company = entry.get("company", "N/A")
        salary = entry.get("salary", "")
        link = entry.get("link", "#")
        applied_date = entry.get("date", "")
        interview_date = entry.get("interviewing_date", "")
        offer_date = entry.get("offer_date", "")
        rejected_date = entry.get("rejected_date", "")
        withdrawn_date = entry.get("withdrawn_date", "")
        notes = entry.get("notes", "")

        # Build date timeline
        timeline = f'<span class="date-chip">Applied: {applied_date}</span>'
        if interview_date:
            timeline += f' <span class="date-chip interview">Interview: {interview_date}</span>'
        if offer_date:
            timeline += f' <span class="date-chip offer">Offer: {offer_date}</span>'
        if rejected_date:
            timeline += f' <span class="date-chip rejected">Rejected: {rejected_date}</span>'
        if withdrawn_date:
            timeline += f' <span class="date-chip withdrawn">Withdrawn: {withdrawn_date}</span>'

        # Status dropdown options
        options_html = ""
        for opt in status_options:
            selected = "selected" if opt == status else ""
            options_html += f'<option value="{opt}" {selected}>{opt.title()}</option>'

        rows_html += f"""
        <tr id="row_{job_id}">
          <td>
            <div class="job-title-cell">
              <a href="{link}" target="_blank">{title}</a>
              {f'<span class="salary-chip">{salary}</span>' if salary and "$" in salary else ""}
            </div>
            <div class="timeline">{timeline}</div>
            {f'<div class="notes">{notes}</div>' if notes and notes not in ("Application submitted successfully", "Dry run — not actually applied") else ""}
          </td>
          <td class="company-cell">{company}</td>
          <td>
            <select class="status-select" onchange="updateStatus('{job_id}', this.value)"
                    style="border-left: 3px solid {color};">
              {options_html}
            </select>
          </td>
        </tr>"""

    if not rows_html:
        rows_html = '<tr><td colspan="3" class="empty">No applications yet — start applying!</td></tr>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Application Tracker</title>
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
    --blue: #3b82f6;
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
    max-width: 1100px;
    margin: 0 auto;
  }}

  header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border);
    padding-bottom: 1.5rem;
    margin-bottom: 2rem;
  }}

  h1 {{
    font-family: var(--mono);
    font-size: 1.4rem;
    color: var(--accent);
  }}

  .nav-links {{
    display: flex;
    gap: 1rem;
  }}

  .nav-links a {{
    font-family: var(--mono);
    font-size: 0.75rem;
    color: var(--muted);
    text-decoration: none;
    border: 1px solid var(--border);
    padding: 0.3rem 0.8rem;
    border-radius: 4px;
    transition: color 0.15s, border-color 0.15s;
  }}

  .nav-links a:hover {{ color: var(--accent); border-color: var(--accent); }}

  /* ── Stats Cards ── */
  .stats-grid {{
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 1rem;
    margin-bottom: 2rem;
  }}

  .stat-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem;
    text-align: center;
  }}

  .stat-value {{
    font-family: var(--mono);
    font-size: 2rem;
    font-weight: 600;
    line-height: 1;
    margin-bottom: 0.4rem;
  }}

  .stat-label {{
    font-size: 0.72rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }}

  .stat-card.total .stat-value {{ color: var(--accent); }}
  .stat-card.active .stat-value {{ color: var(--blue); }}
  .stat-card.interviewing .stat-value {{ color: var(--yellow); }}
  .stat-card.offers .stat-value {{ color: var(--green); }}
  .stat-card.rate .stat-value {{ color: var(--accent2); }}

  /* ── Table ── */
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

  .count {{
    background: var(--surface2);
    border: 1px solid var(--border);
    color: var(--accent);
    font-size: 0.7rem;
    padding: 0.1rem 0.5rem;
    border-radius: 20px;
  }}

  table {{
    width: 100%;
    border-collapse: collapse;
    background: var(--surface);
    border-radius: 10px;
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

  tbody tr {{
    border-bottom: 1px solid var(--border);
    transition: background 0.15s;
  }}

  tbody tr:last-child {{ border-bottom: none; }}
  tbody tr:hover {{ background: var(--surface2); }}

  td {{
    padding: 0.85rem 1rem;
    vertical-align: top;
  }}

  .job-title-cell a {{
    color: var(--text);
    text-decoration: none;
    font-weight: 600;
    font-size: 0.9rem;
  }}

  .job-title-cell a:hover {{ color: var(--accent); }}

  .company-cell {{
    color: var(--muted);
    font-size: 0.85rem;
    white-space: nowrap;
  }}

  .salary-chip {{
    display: inline-block;
    font-family: var(--mono);
    font-size: 0.65rem;
    color: var(--green);
    border: 1px solid #166534;
    background: #0f2318;
    padding: 0.1rem 0.4rem;
    border-radius: 4px;
    margin-left: 0.5rem;
    vertical-align: middle;
  }}

  /* ── Timeline dates ── */
  .timeline {{
    margin-top: 0.4rem;
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
  }}

  .date-chip {{
    font-family: var(--mono);
    font-size: 0.65rem;
    color: var(--muted);
    background: var(--surface2);
    border: 1px solid var(--border);
    padding: 0.1rem 0.5rem;
    border-radius: 4px;
  }}

  .date-chip.interview {{ color: var(--yellow); border-color: #78350f; background: #1c1200; }}
  .date-chip.offer {{ color: var(--green); border-color: #166534; background: #0f2318; }}
  .date-chip.rejected {{ color: var(--red); border-color: #7f1d1d; background: #1c0000; }}
  .date-chip.withdrawn {{ color: var(--muted); border-color: var(--border); }}

  .notes {{
    font-size: 0.75rem;
    color: var(--muted);
    margin-top: 0.3rem;
    font-style: italic;
  }}

  /* ── Status dropdown ── */
  .status-select {{
    background: var(--surface2);
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.35rem 0.6rem;
    font-family: var(--sans);
    font-size: 0.8rem;
    cursor: pointer;
    width: 100%;
    outline: none;
  }}

  .status-select:hover {{ border-color: var(--accent); }}

  .empty {{
    color: var(--muted);
    text-align: center;
    padding: 3rem;
    font-style: italic;
  }}

  /* ── Toast ── */
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

  .date-tag {{
    font-family: var(--mono);
    font-size: 0.75rem;
    color: var(--muted);
  }}
</style>
</head>
<body>

<header>
  <div>
    <h1>📊 Application Tracker</h1>
    <div class="date-tag">{today}</div>
  </div>
  <nav class="nav-links">
    <a href="http://localhost:8765">⚡ Daily Briefing</a>
    <a href="http://localhost:8765/dashboard">🔄 Refresh</a>
  </nav>
</header>

<!-- ── Stats ── -->
<div class="stats-grid">
  <div class="stat-card total">
    <div class="stat-value">{total}</div>
    <div class="stat-label">Total Applied</div>
  </div>
  <div class="stat-card active">
    <div class="stat-value">{active}</div>
    <div class="stat-label">Active</div>
  </div>
  <div class="stat-card interviewing">
    <div class="stat-value">{counts['interviewing']}</div>
    <div class="stat-label">Interviewing</div>
  </div>
  <div class="stat-card offers">
    <div class="stat-value">{counts['offer']}</div>
    <div class="stat-label">Offers</div>
  </div>
  <div class="stat-card rate">
    <div class="stat-value">{response_rate}%</div>
    <div class="stat-label">Response Rate</div>
  </div>
</div>

<!-- ── Applications Table ── -->
<h2>📋 All Applications <span class="count">{total}</span></h2>
<table>
  <thead>
    <tr>
      <th>Position</th>
      <th>Company</th>
      <th>Status</th>
    </tr>
  </thead>
  <tbody>
    {rows_html}
  </tbody>
</table>

<div id="toast"></div>

<script>
  function showToast(msg) {{
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.style.display = 'block';
    setTimeout(() => t.style.display = 'none', 2500);
  }}

  function updateStatus(jobId, newStatus) {{
    const today = new Date().toLocaleDateString();
    fetch('http://localhost:8765/update-status', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{job_id: jobId, status: newStatus, date: today}})
    }}).then(r => r.json()).then(data => {{
      if (data.ok) {{
        showToast('✅ Status updated to ' + newStatus);
      }}
    }}).catch(err => {{
      showToast('❌ Error updating status');
      console.log(err);
    }});
  }}
</script>
</body>
</html>"""