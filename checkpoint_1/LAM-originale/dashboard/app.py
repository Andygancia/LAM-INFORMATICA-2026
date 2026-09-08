import errno
import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from simulation import DEFAULT_PARAMS, simula_mercato


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
HOST = "127.0.0.1"
DEFAULT_PORT = 8765


class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def end_headers(self):
        # Gli asset statici cambiano spesso in sviluppo: forziamo la
        # rivalidazione così non serve piu il parametro ?v= manuale.
        if not self.path.startswith("/api/"):
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def do_GET(self):
        if self.path == "/":
            self.path = "/index.html"
        if self.path == "/api/defaults":
            self.send_json(DEFAULT_PARAMS)
            return
        super().do_GET()

    def do_POST(self):
        if self.path != "/api/simulate":
            self.send_error(404, "Endpoint non trovato")
            return

        length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(length) if length else b"{}"

        try:
            payload = json.loads(raw_body.decode("utf-8"))
            result = simula_mercato(payload)
            self.send_json(result)
        except Exception as exc:
            self.send_json({"error": str(exc)}, status=400)

    def send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    requested_port = int(os.environ.get("PORT", DEFAULT_PORT))
    last_error = None

    for port in range(requested_port, requested_port + 20):
        try:
            server = ThreadingHTTPServer((HOST, port), DashboardHandler)
            break
        except OSError as exc:
            last_error = exc
            if exc.errno not in (errno.EADDRINUSE, errno.EACCES, errno.EPERM):
                raise
    else:
        raise RuntimeError(
            f"Impossibile avviare la dashboard da porta {requested_port} "
            f"a {requested_port + 19}: {last_error}"
        ) from last_error

    print(f"Dashboard disponibile su http://{HOST}:{server.server_port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
