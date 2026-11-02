import os
import csv
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEMO_FILE = os.path.join(BASE_DIR, "demo.csv")

def search_csv(target):
    if not os.path.exists(DEMO_FILE):
        raise FileNotFoundError("demo.csv tidak ditemukan")

    with open(DEMO_FILE, "r", encoding="cp1251", newline="") as f:
        reader = csv.DictReader(f, delimiter="|")

        for row in reader:
            user_id = str(row.get("User_ID", "")).strip()
            if user_id == target:
                return {
                    "User_ID": user_id,
                    "Status": "DUMMY"
                }

    return None


class handler(BaseHTTPRequestHandler):

    def send_json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if parsed.path in ("/", "/api/health"):
            return self.send_json(200, {
                "status": "online",
                "name": "Telegram API"
            })

        if parsed.path == "/api/search":
            target = params.get("id", [""])[0].strip()

            if not target:
                return self.send_json(400, {
                    "status": "error",
                    "message": "Parameter id wajib diisi"
                })

            try:
                result = search_csv(target)

                return self.send_json(200, {
                    "status": "success",
                    "found": result is not None,
                    "data": result
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