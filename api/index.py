import json
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):

    def send_json(self, status, data):
        body = json.dumps(data).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]

        if path in ("/api", "/api/"):
            return self.send_json(200, {
                "status": "online",
                "name": "Telegram API",
                "version": "1.0.0",
                "mode": "synthetic_demo",
                "endpoints": [
                    "/api",
                    "/api/health"
                ]
            })

        if path == "/api/health":
            return self.send_json(200, {
                "status": "healthy"
            })

        return self.send_json(404, {
            "status": "error",
            "message": "Endpoint not found"
        })