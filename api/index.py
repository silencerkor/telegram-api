
import os
import csv
import io
import json
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

GITHUB_OWNER = "silencerkor"
GITHUB_REPO = "telegram-api"
GITHUB_BRANCH = "main"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

PART_COUNT = 25
PART_PATH = "parts/Telegram_csv.part{:03d}"

def read_part(part_number):
    if not GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN belum dipasang di Vercel")

    path = PART_PATH.format(part_number)
    url = (
        f"https://api.github.com/repos/{GITHUB_OWNER}/"
        f"{GITHUB_REPO}/contents/{path}?ref={GITHUB_BRANCH}"
    )

    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.raw+json",
            "User-Agent": "Telegram-Synthetic-API"
        }
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", errors="replace")

class handler(BaseHTTPRequestHandler):
    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if parsed.path == "/api/health":
            return self.send_json(200, {
                "status": "online",
                "mode": "synthetic_demo"
            })

        if parsed.path not in ("/api", "/api/search"):
            return self.send_json(404, {"error": "Endpoint not found"})

        search_id = params.get("id", [""])[0].strip()

        if not search_id:
            return self.send_json(400, {
                "status": "error",
                "message": "Masukkan parameter id"
            })

        try:
            found = False
            checked = 0

            for number in range(1, PART_COUNT + 1):
                content = read_part(number)
                reader = csv.DictReader(
                    io.StringIO(content),
                    delimiter="|"
                )

                if not reader.fieldnames:
                    continue

                id_column = next(
                    (column for column in reader.fieldnames
                     if column.strip().lower() in
                     ("user_id", "userid", "id")),
                    None
                )

                if not id_column:
                    continue

                for row in reader:
                    checked += 1
                    if str(row.get(id_column, "")).strip() == search_id:
                        found = True
                        break

                if found:
                    break

            return self.send_json(200, {
                "status": "success",
                "found": found,
                "query": search_id,
                "records_checked": checked,
                "mode": "synthetic_demo"
            })

        except Exception as error:
            return self.send_json(500, {
                "status": "error",
                "message": str(error)
            })
