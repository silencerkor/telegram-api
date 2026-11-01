
import json
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

OWNER = "silencerkor"
REPO = "telegram-api"
BRANCH = "main"

PARTS = [
    f"Telegram_csv.part{i:03d}"
    for i in range(1, 26)
]

class handler(BaseHTTPRequestHandler):

    def send_json(self, status, data):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_github_file(self, filename):
        url = (
            f"https://raw.githubusercontent.com/"
            f"{OWNER}/{REPO}/{BRANCH}/parts/{filename}"
        )

        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Telegram-Synthetic-API"}
        )

        with urllib.request.urlopen(request, timeout=20) as response:
            return response.read()

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if parsed.path in ("/api", "/api/"):
            return self.send_json(200, {
                "status": "online",
                "name": "Telegram API",
                "mode": "synthetic_demo",
                "endpoints": [
                    "/api/health",
                    "/api/search?id=10001"
                ]
            })

        if parsed.path == "/api/health":
            return self.send_json(200, {
                "status": "healthy"
            })

        if parsed.path == "/api/search":
            search_id = params.get("id", [""])[0].strip()

            if not search_id.isdigit():
                return self.send_json(400, {
                    "status": "error",
                    "message": "ID harus berupa angka"
                })

            checked = 0
            missing = []

            for filename in PARTS:
                try:
                    content = self.read_github_file(filename)
                    checked += 1

                    # Memeriksa batas baris dengan aman.
                    for line in content.splitlines():
                        columns = line.decode(
                            "utf-8", errors="replace"
                        ).split("|")

                        if len(columns) >= 5:
                            if columns[4].strip() == search_id:
                                return self.send_json(200, {
                                    "status": "success",
                                    "user_id": search_id,
                                    "record": "FOUND",
                                    "source": filename,
                                    "mode": "synthetic_demo"
                                })

                except urllib.error.HTTPError as error:
                    if error.code == 404:
                        missing.append(filename)
                        continue

                    return self.send_json(502, {
                        "status": "error",
                        "message": "GitHub gagal diakses",
                        "http_status": error.code
                    })

                except Exception:
                    return self.send_json(502, {
                        "status": "error",
                        "message": "Gagal membaca file GitHub"
                    })

            if missing:
                return self.send_json(502, {
                    "status": "error",
                    "message": "Sebagian file GitHub tidak tersedia",
                    "files_checked": checked,
                    "missing_files": missing
                })

            return self.send_json(404, {
                "status": "not_found",
                "message": "ID tidak ditemukan"
            })

        return self.send_json(404, {
            "status": "error",
            "message": "Endpoint not found"
        }) 
