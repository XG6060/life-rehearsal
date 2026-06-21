"""One-command server: 3D model + scene + Streamlit"""
import http.server, socketserver, subprocess, sys, threading, time
from pathlib import Path

PORT = 8090
DIR = Path(__file__).parent / "ui" / "static"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIR), **kwargs)
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()
    def log_message(self, fmt, *args):
        pass

def run_server():
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"[model server] http://localhost:{PORT}")
        httpd.serve_forever()

if __name__ == '__main__':
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    time.sleep(0.3)
    print("[streamlit] starting...")
    subprocess.run([sys.executable, "-m", "streamlit", "run", "ui/app.py"])
