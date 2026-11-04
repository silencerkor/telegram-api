from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import os
import mmap

CSV_FILE = os.path.join(os.path.dirname(__file__), "..", "Telegram_27.csv")
SEP = "|"
MAX_RESULTS = 20

def get_header(filepath, sep):
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        return f.readline().rstrip("\n\r").split(sep)

def search_mmap(filepath, query, sep, header, max_results=20):
    results = []
    query_bytes = query.lower().encode("utf-8", errors="replace")
    line_num = 0
    with open(filepath, "rb") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        mm.readline()  # skip header
        line_num = 1
        while True:
            line_bytes = mm.readline()
            if not line_bytes:
                break
            line_num += 1
            if query_bytes in line_bytes.lower():
                line = line_bytes.decode("utf-8", errors="replace").rstrip("\n\r")
                parts = line.split(sep)
                while len(parts) < len(header):
                    parts.append("")
                results.append(dict(zip(header, [v.strip() for v in parts])))
                if len(results) >= max_results:
                    break
        mm.close()
    return results

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        query = params.get("q", [None])[0]

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        if not query or len(query.strip()) < 3:
            resp = {"status": "error", "message": "Parameter ?q= minimal 3 karakter"}
            self.wfile.write(json.dumps(resp).encode())
            return

        if not os.path.exists(CSV_FILE):
            resp = {"status": "error", "message": "CSV file tidak ditemukan di server"}
            self.wfile.write(json.dumps(resp).encode())
            return

        try:
            header = get_header(CSV_FILE, SEP)
            results = search_mmap(CSV_FILE, query.strip(), SEP, header, MAX_RESULTS)
            resp = {
                "status": "ok",
                "query": query.strip(),
                "total": len(results),
                "results": results
            }
        except Exception as e:
            resp = {"status": "error", "message": str(e)}

        self.wfile.write(json.dumps(resp, ensure_ascii=False).encode())

    def log_message(self, format, *args):
        pass  # suppress access logs