
import os
import json
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse

OWNER = "silencerkor"
REPO = "telegram-api"
BRANCH = "main"
TOKEN = os.environ.get("GITHUB_TOKEN")

TOTAL_PARTS = 25
PREFIX = "Telegram_csv.part"


def github_request(filename):
    if not TOKEN:
        raise RuntimeError("GITHUB_TOKEN belum tersedia")

    url = (
        f"https://api.github.com/repos/{OWNER}/{REPO}"
        f"/contents/parts/{filename}?ref={BRANCH}"
    )

    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "Telegram-Synthetic-API"
        }
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def check_parts():
    results = []
    total_size = 0

    for number in range(1, TOTAL_PARTS + 1):
        filename = f"{PREFIX}{number:03d}"

        try:
            data = github_request(filename)

            size = data.get("size", 0)
            total_size += size

            results.append({
                "file": filename,
                "exists": True,
                "size_bytes": size,
                "type": data.get("type")
            })

        except urllib.error.HTTPError as error:
            results.append({
                "file": filename,
                "exists": False,
                "http_status": error.code
            })

    return {
        "total_parts": TOTAL_PARTS,
        "found_parts": sum(1 for item in results if item["exists"]),
        "total_size_bytes": total_size,
        "files": results
    }


class handler(BaseHTTPRequestHandler):

    def send_json(self, status, data):
        body = json.dumps(
            data,
            ensure_ascii=False,
            indent=2
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
        path = urlparse(self.path).path

        if path in ("/", "/api/health"):
            return self.send_json(200, {
                "status": "online",
                "name": "Telegram API",
                "mode": "synthetic_demo",
                "endpoints": [
                    "/api/health",
                    "/api/diagnostic"
                ]
            })

        if path == "/api/diagnostic":
            try:
                result = check_parts()

                return self.send_json(200, {
                    "status": "success",
                    "repository": f"{OWNER}/{REPO}",
                    "branch": BRANCH,
                    **result
                })

            except Exception as error:
                return self.send_json(500, {
                    "status": "error",
                    "message": str(error)
                })

        return self.send_json(404, {
            "status": "error",
            "message": "Endpoint tidak ditemukan"
        })
