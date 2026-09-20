import argparse
import json
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FRAMES = os.path.join(ROOT, "data", "frames")

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def log_message(self, fmt, *args):
        pass

    def _json(self, code, payload):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.send_header("access-control-allow-origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("access-control-allow-origin", "*")
        self.send_header("access-control-allow-headers", "content-type")
        self.send_header("access-control-allow-methods", "POST, OPTIONS")
        self.end_headers()

    def do_POST(self):
        if self.path.rstrip("/") != "/api/scan":
            return self._json(404, {"error": "unknown route"})
        try:
            length = int(self.headers.get("content-length", "0"))
            req = json.loads(self.rfile.read(length) or b"{}")
        except ValueError as e:
            return self._json(400, {"error": f"bad JSON: {e}"})

        name = os.path.basename(req.get("frame", ""))
        path = os.path.join(FRAMES, name)
        if not name or not os.path.isfile(path):
            return self._json(400, {"error": f"no such frame: {name!r}"})

        try:
            from PIL import Image

            import gridscan
        except ImportError as e:
            return self._json(503, {"error": f"live scanning needs Pillow: {e}"})

        reference = None
        ref_name = req.get("reference")
        if ref_name:
            ref_path = os.path.join(ROOT, "data", "refs", os.path.basename(ref_name) + ".jpg")
            if not os.path.isfile(ref_path):
                return self._json(400, {"error": f"no such reference: {ref_name!r}"})
            reference = Image.open(ref_path)

        try:
            probs = gridscan.scan(
                Image.open(path),
                req.get("target") or "",
                cols=int(req.get("cols", 5)),
                rows=int(req.get("rows", req.get("cols", 5))),
                seed=int(req.get("seed", 7)),
                hint=req.get("hint"),
                reference=reference,
                channel=req.get("channel", "attached"),
            )
        except Exception as e:
            return self._json(502, {"error": str(e)[:400]})
        return self._json(200, {"frame": name, "probs": probs})

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8020)
    args = ap.parse_args()
    print(f"http://{args.host}:{args.port}  -> {os.environ.get('DJEV_URL', 'http://127.0.0.1:8011')}")
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()

if __name__ == "__main__":
    main()
