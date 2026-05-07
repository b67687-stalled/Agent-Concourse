
class ParleyHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        if args[1] != 200:
            msg = f"[{self.log_date_time_string()}] {args[0]} - {format % args}"
            print(msg, file=sys.stderr)

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _send_file(self, path: Path, content_type: str):
        if not path.exists():
            self._send_json({"error": "Not found"}, 404)
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(path.read_bytes())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/api/pool":
            self._send_json({"models": MODEL_POOL, "count": len(MODEL_POOL)})
        elif path == "/" or path == "":
            self._send_file(STATIC_DIR / "index.html", "text/html; charset=utf-8")
        else:
            fpath = STATIC_DIR / path.lstrip("/")
            if fpath.exists() and fpath.is_file():
                ext = fpath.suffix.lower()
                ctype = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
                         ".js": "application/javascript; charset=utf-8", ".png": "image/png"}.get(ext, "application/octet-stream")
                self._send_file(fpath, ctype)
            else:
                self._send_file(STATIC_DIR / "index.html", "text/html; charset=utf-8")

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON"}, 400)
            return
        if self.path == "/api/key-check":
            self._send_json({"has_key": bool(OPENROUTER_API_KEY)})
        else:
            self._send_json({"error": "Not found"}, 404)

def main():
    port = 8080
    if len(sys.argv) > 1 and sys.argv[1] == "--port":
        port = int(sys.argv[2])
    index_html = STATIC_DIR / "index.html"
    if not index_html.exists():
        print(f"ERROR: Frontend file not found at {index_html}", file=sys.stderr)
        sys.exit(1)
    print(f"  Parley on http://localhost:{port}")
    class ThreadedServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
        allow_reuse_address = True
        daemon_threads = True
    server = ThreadedServer(("0.0.0.0", port), ParleyHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Shutting down...")
        server.shutdown()

if __name__ == "__main__":
    main()
