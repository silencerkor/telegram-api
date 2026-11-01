
import csv
import glob
import json
import os
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "parts")


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
            user_id = params.get("id", [""])[0].strip()

            if not user_id.isdigit():
                return self.send_json(400, {
                    "status": "error",
                    "message": "Masukkan ID angka yang valid"
                })

            # Hanya membaca berkas CSV demo yang sudah disanitasi.
            files = sorted(glob.glob(
                os.path.join(BASE_DIR, "*.csv")
            ))

            if not files:
                return self.send_json(503, {
                    "status": "error",
                    "message": "File CSV demo tidak tersedia"
                })

            for file_path in files:
                try:
                    with open(
                        file_path,
                        "r",
                        encoding="utf-8-sig",
                        newline=""
                    ) as file:
                        reader = csv.reader(file, delimiter="|")

                        for row in reader:
                            if len(row) < 5:
                                continue

                            if row[4].strip() == user_id:
                                return self.send_json(200, {
                                    "status": "success",
                                    "mode": "synthetic_demo",
                                    "data": {
                                        "user_id": user_id,
                                        "record": "SYNTHETIC",
                                        "source": os.path.basename(file_path)
                                    }
                                })

                except (OSError, UnicodeError):
                    continue

            return self.send_json(404, {
                "status": "not_found",
                "message": "ID tidak ditemukan"
            })

        return self.send_json(404, {
            "status": "error",
            "message": "Endpoint not found"
        })
