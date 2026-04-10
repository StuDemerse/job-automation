"""
approval_server.py — A lightweight local web server that handles
approve/skip/remove button clicks from the daily briefing report.

Run this alongside your report:
    python approval_server.py

Then open your briefing report in the browser and the buttons will work.
It runs on http://localhost:8765 in the background.
"""

import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from report_generator import load_approved_jobs, save_approved_jobs
from dashboard import build_dashboard, load_applications_log

PORT = 8765
REPORT_DIR = "./reports"


class ApprovalHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        """Suppress default server logs — keep terminal clean."""
        pass

    def send_json(self, data: dict, status: int = 200):
        """Helper to send a JSON response."""
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        """Handle browser preflight CORS requests."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        """Serve the HTML report files."""
	# Serve live approved jobs list
        if self.path == "/approved-jobs":
            approved = load_approved_jobs()
            approved_jobs = {k: v for k, v in approved.items() if v.get("status") == "approved"}
            self.send_json({"jobs": approved_jobs, "count": len(approved_jobs)})
            return
        if self.path == "/" or self.path == "":
            # Find and serve the latest report
            try:
                files = sorted([
                    f for f in os.listdir(REPORT_DIR)
                    if f.endswith(".html")
                ])
                if files:
                    self.path = f"/{files[-1]}"
                else:
                    self.send_json({"error": "No reports found"}, 404)
                    return
            except Exception as e:
                self.send_json({"error": str(e)}, 500)
                return
	
	# Serve dashboard page
        if self.path == "/dashboard":
            dashboard_html = build_dashboard()
            body = dashboard_html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # Serve applications log as JSON
        if self.path == "/applications":
            from dashboard import load_applications_log as _load_log
            log = _load_log()
            self.send_json({"applications": log, "count": len(log)})
            return

        # Update application status
        if self.path == "/update-status":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            data = json.loads(body)
            log = load_applications_log()
            job_id = data.get("job_id")
            new_status = data.get("status")
            update_date = data.get("date", "")
            for entry in log:
                if entry.get("job_id") == job_id:
                    entry["status"] = new_status
                    entry[f"{new_status}_date"] = update_date
                    break
            save_applications_log(log)
            print(f"  📊 Status updated: {job_id} → {new_status}")
            self.send_json({"ok": True})
            return

        # Serve report files
        filepath = os.path.join(REPORT_DIR, self.path.lstrip("/"))
        if os.path.exists(filepath) and filepath.endswith(".html"):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            # Inject the server port so buttons know where to POST
            content = content.replace(
                "fetch('/approve'",
                f"fetch('http://localhost:{PORT}/approve'"
            ).replace(
                "fetch('/skip'",
                f"fetch('http://localhost:{PORT}/skip'"
            ).replace(
                "fetch('/remove'",
                f"fetch('http://localhost:{PORT}/remove'"
            )
            body = content.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_json({"error": "File not found"}, 404)

    def do_POST(self):
        """Handle approve / skip / remove actions."""
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "Invalid JSON"}, 400)
            return

        approved = load_approved_jobs()

        if self.path == "/approve":
            job_id = data.get("jobId")
            if job_id:
                approved[job_id] = {
                    "status":  "approved",
                    "title":   data.get("title", ""),
                    "company": data.get("company", ""),
                    "salary":  data.get("salary", ""),
                    "link":    data.get("link", ""),
                    "date":    data.get("date", ""),
                }
                save_approved_jobs(approved)
                print(f"  ✅ Approved: {data.get('title')} @ {data.get('company')}")
                self.send_json({"ok": True})
            else:
                self.send_json({"ok": False, "error": "Missing jobId"}, 400)

        elif self.path == "/skip":
            job_id = data.get("jobId")
            if job_id:
                approved[job_id] = {"status": "skipped"}
                save_approved_jobs(approved)
                print(f"  ❌ Skipped job: {job_id}")
                self.send_json({"ok": True})
            else:
                self.send_json({"ok": False, "error": "Missing jobId"}, 400)

        elif self.path == "/remove":
            job_id = data.get("jobId")
            if job_id and job_id in approved:
                del approved[job_id]
                save_approved_jobs(approved)
                print(f"  🗑️  Removed from queue: {job_id}")
                self.send_json({"ok": True})
            else:
                self.send_json({"ok": False, "error": "Job not found"}, 400)

        else:
            self.send_json({"ok": False, "error": "Unknown endpoint"}, 404)


def run():
    server = HTTPServer(("localhost", PORT), ApprovalHandler)
    print(f"""
╔══════════════════════════════════════════════╗
║       Approval Server Running               ║
║       http://localhost:{PORT}               ║
╚══════════════════════════════════════════════╝

Open your briefing at: http://localhost:{PORT}
Approve or skip jobs using the buttons.
Press Ctrl+C to stop.
""")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped.")


if __name__ == "__main__":
    run()