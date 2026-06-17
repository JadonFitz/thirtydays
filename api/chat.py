"""Vercel serverless function — proxies chat requests to Anthropic API.
Requires ANTHROPIC_API_KEY set in Vercel project environment variables.
"""
from http.server import BaseHTTPRequestHandler
import json, os, urllib.request, urllib.error


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self._cors(200)

    def do_POST(self):
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            self._json({"error": "ANTHROPIC_API_KEY not configured in Vercel env vars"}, 500)
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
        except Exception as e:
            self._json({"error": f"Bad request: {e}"}, 400)
            return

        messages = body.get("messages", [])
        system = body.get("system", "You are a helpful research assistant.")

        payload = json.dumps({
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 1024,
            "system": system,
            "messages": [{"role": m["role"], "content": m["content"]} for m in messages],
        }).encode()

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
            reply = data["content"][0]["text"]
            self._json({"reply": reply})
        except urllib.error.HTTPError as e:
            err = e.read().decode()
            self._json({"error": f"Anthropic API error {e.code}: {err}"}, 502)
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _cors(self, code=200):
        self.send_response(code)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_):
        pass
