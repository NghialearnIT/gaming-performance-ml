"""Serve the frontend demo on this computer and open it in the default browser."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Timer
import webbrowser

ADDRESS = ("127.0.0.1", 5500)
DEMO_URL = "http://127.0.0.1:5500/?demo=1"


def main():
    handler = partial(SimpleHTTPRequestHandler, directory=Path(__file__).resolve().parent)
    try:
        server = ThreadingHTTPServer(ADDRESS, handler)
    except OSError as error:
        print(f"Không mở được cổng 5500 ({error}).")
        print("Nếu đang mở PowerShell chạy bản demo cũ, nhấn Ctrl+C tại đó rồi thử lại.")
        return 1

    print(f"Đang chạy {DEMO_URL}")
    print("Giữ cửa sổ này mở khi dùng demo. Nhấn Ctrl+C để dừng.")
    with server:
        opener = Timer(0.3, webbrowser.open, args=(DEMO_URL,))
        opener.daemon = True
        opener.start()
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
