
import os
import csv
import io
import json
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

OWNER = "silencerkor"
REPO = "telegram-api"
BRANCH = "main"
TOKEN = os.environ.get("GITHUB_TOKEN")

TOTAL_PARTS = 25
FILE_PREFIX = "Telegram_csv.part"

def fetch_part(number):
    if not TOKEN:
        raise RuntimeError("GITHUB_TOKEN belum dipasang di Vercel")

    filename = f"{FILE_PREFIX}{number:03d}"
    url = (
        f"https://api.github.com/repos/{OWNER}/{REPO}"
        f"/contents/parts/{filename}?ref={BRANCH}"
    )

    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github.raw+json",
            "User-Agent": "Telegram-API"
        }
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def search_dataset(target):
    checked = 0

    for number in range(1, TOTAL_PARTS + 1):
        content = fetch_part(number)

        reader = csv.DictReader(
            io.StringIO(content, newline=""),
            delimiter="|"
        )

        if not reader.fieldnames:
            continue

        id_column = next(
            (
                name for name in reader.fieldnames
                if name.strip().lower() in
                ("user_id", "userid", "id")
            ),
            None
        )

        if not id_column:
            continue

        for row in reader:
            checked += 1

            if str(row.get(id_column, "")).strip() == target:
                return True, checked

    return False, checked


class handler(BaseHTTPRequestHandler):

    def send_json(self, status, data):
        body = json.dumps(
            data,
            ensure_ascii=False
        ).encode("utf-8")

        self.send_response(status)
        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if parsed.path == "/api/health":
            return self.send_json(200, {
                "status": "online",
                "name": "Telegram API",
                "mode": "synthetic_demo"
            })

        if parsed.path not in ("/", "/api", "/api/search"):
            return self.send_json(404, {
                "status": "error",
                "message": "Endpoint tidak ditemukan"
            })

        target = params.get("id", [""])[0].strip()

        if not target:
            return self.send_json(400, {
                "status": "error",
                "message": "Masukkan parameter id",
                "example": "/api/search?id=10001"
            })

        try:
            found, checked = search_dataset(target)

            return self.send_json(200, {
                "status": "success",
                "mode": "synthetic_demo",
                "found": found,
                "query": target,
                "records_checked": checked
            })

        except Exception as error:
            return self.send_json(500, {
                "status": "error",
                "message": str(error)
            })
