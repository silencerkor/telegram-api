
import csv
import io
import json
import urllib.request
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

GITHUB_RAW = (
    "https://raw.githubusercontent.com/"
    "silencerkor/telegram-api/main/parts/demo.csv"
)

class handler(BaseHTTPRequestHandler):

    def send_json(self, status, data):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

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

            try:
                request = urllib.request.Request(
                    GITHUB_RAW,
                    headers={"User-Agent": "Synthetic-Demo-API"}
                )

                with urllib.request.urlopen(
                    request, timeout=15
                ) as response:
                    content = response.read().decode("utf-8")

                reader = csv.DictReader(
                    io.StringIO(content),
                    delimiter="|"
                )

                for row in reader:
                    if row.get("id", "").strip() == search_id:
                        return self.send_json(200, {
                            "status": "success",
                            "mode": "synthetic_demo",
                            "data": {
                                "id": search_id,
                                "name": row.get("name", ""),
                                "username": row.get("username", ""),
                                "phone": row.get("phone", "")
                            }
                        })

                return self.send_json(404, {
                    "status": "not_found",
                    "message": "ID tidak ditemukan"
                })

            except Exception:
                return self.send_json(502, {
                    "status": "error",
                    "message": "Gagal membaca file demo GitHub"
                })

        return self.send_json(404, {
            "status": "error",
            "message": "Endpoint not found"
        })
