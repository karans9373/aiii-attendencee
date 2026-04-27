from __future__ import annotations

import threading
import time
import webbrowser

from app import app


def run_server() -> None:
    app.run(port=5050, debug=False, use_reloader=False)


def main() -> None:
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(1.2)

    try:
        import webview

        webview.create_window("WorkPulse AI", "http://127.0.0.1:5050/")
        webview.start()
    except ImportError:
        webbrowser.open("http://127.0.0.1:5050/")
        print("pywebview is not installed, so the app opened in your browser instead.")
        print("Install it with: pip install pywebview")
        server_thread.join()


if __name__ == "__main__":
    main()
