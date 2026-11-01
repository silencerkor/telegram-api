
import glob
import json
import os
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "parts")
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

            files = sorted(glob.glob(
                os.path.join(
                    BASE_DIR,
                    "Telegram_csv.part[0-9][0-9][0-9]"
                )
            ))

            if not files:
                return self.send_json(503, {
                    "status": "error",
                    "message": "File parts tidak tersedia"
                })

            for path in files:
                try:
                    with open(path, "rb") as file:
                        for line in file:
                            columns = line.decode(
                                "utf-8",
                                errors="replace"
                            ).rstrip("\r\n").split("|")

                            if len(columns) >= 5:
                                if columns[4].strip() == search_id:
                                    return self.send_json(200, {
                                        "status": "success",
                                        "mode": "synthetic_demo",
                                        "data": {
                                            "user_id": search_id,
                                            "record": "FOUND"
                                        }
                                    })

                except OSError:
                    continue

            return self.send_json(404, {
                "status": "not_found",
                "message": "ID tidak ditemukan"
            })

        return self.send_json(404, {
            "status": "error",
            "message": "Endpoint not found"
        })
