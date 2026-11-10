"""Vercel serverless function: start the Auto Research workflow from the dashboard.

GET  /api/research  -> status of the latest Auto Research run
POST /api/research  -> start a run on main (body: {"topics": "optional, comma separated"})

Both need the dashboard passcode in the X-Passcode header.

Environment variables (Vercel project settings):
  RESEARCH_PASSCODE      passcode typed into the dashboard
  GITHUB_DISPATCH_TOKEN  fine-grained GitHub token for this repo only,
                         with "Actions: Read and write" permission
  GITHUB_REPO            optional, defaults to JadonFitz/thirtydays

The token never leaves the server and responses carry only run status.
"""
from http.server import BaseHTTPRequestHandler
import hmac, json, os, time, urllib.error, urllib.request

WORKFLOW = "research-auto.yml"
BRANCH = "main"
MAX_TOPICS_CHARS = 300
ACTIVE = {"queued", "in_progress", "waiting", "requested", "pending"}


def _github(method, path, token, body=None):
    repo = os.environ.get("GITHUB_REPO", "JadonFitz/thirtydays")
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}{path}",
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "thirtydays-dashboard",
            "Content-Type": "application/json",
        },
        method=method,
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read()
        return json.loads(raw) if raw else {}


def _latest_run(token):
    data = _github("GET", f"/actions/workflows/{WORKFLOW}/runs?per_page=1", token)
    runs = data.get("workflow_runs") or []
    if not runs:
        return None
    r = runs[0]
    return {
        "status": r.get("status"),
        "conclusion": r.get("conclusion"),
        "event": r.get("event"),
        "created_at": r.get("created_at"),
        "updated_at": r.get("updated_at"),
        "url": r.get("html_url"),
    }


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        token = self._authorize()
        if not token:
            return
        try:
            self._json({"run": _latest_run(token)})
        except urllib.error.HTTPError as e:
            self._json({"error": f"GitHub returned {e.code} when reading run status"}, 502)
        except Exception:
            self._json({"error": "Couldn't reach GitHub"}, 502)

    def do_POST(self):
        token = self._authorize()
        if not token:
            return
        try:
            length = min(int(self.headers.get("Content-Length", 0) or 0), 4096)
            body = json.loads(self.rfile.read(length) or b"{}")
            topics = str(body.get("topics", "") or "").strip()
        except Exception:
            self._json({"error": "Bad request"}, 400)
            return
        if len(topics) > MAX_TOPICS_CHARS:
            self._json({"error": f"Topics are limited to {MAX_TOPICS_CHARS} characters"}, 400)
            return

        try:
            latest = _latest_run(token)
            if latest and latest["status"] in ACTIVE:
                self._json({"error": "A research run is already going", "run": latest}, 409)
                return
            _github(
                "POST",
                f"/actions/workflows/{WORKFLOW}/dispatches",
                token,
                {"ref": BRANCH, "inputs": {"topics": topics}},
            )
        except urllib.error.HTTPError as e:
            self._json({"error": f"GitHub returned {e.code} when starting the run"}, 502)
            return
        except Exception:
            self._json({"error": "Couldn't reach GitHub"}, 502)
            return
        self._json({"started": True}, 202)

    def _authorize(self):
        """Return the GitHub token if the passcode matches, else send an error."""
        expected = os.environ.get("RESEARCH_PASSCODE", "")
        token = os.environ.get("GITHUB_DISPATCH_TOKEN", "")
        if not expected or not token:
            self._json({"error": "The run button isn't set up yet"}, 503)
            return None
        given = self.headers.get("X-Passcode", "")
        if not hmac.compare_digest(given.encode(), expected.encode()):
            time.sleep(1)  # slow down guessing
            self._json({"error": "Wrong passcode"}, 401)
            return None
        return token

    def _json(self, obj, code=200):
        out = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *_):
        pass
