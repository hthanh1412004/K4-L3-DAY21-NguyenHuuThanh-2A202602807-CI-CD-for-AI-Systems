"""Capture the actual local MLflow page using Chromium's DevTools protocol.

Needs websocket-client in the Python interpreter running this optional helper.
The PNG captures page content; take a browser-window screenshot manually for
the rubric's additional address-bar requirement.
"""
import argparse
import base64
import json
import subprocess
import time
import urllib.request
from pathlib import Path

import websocket


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--browser", required=True)
    parser.add_argument("--url", default="http://localhost:5000/#/experiments/1")
    args = parser.parse_args()
    profile = Path("outputs/mlflow-browser").resolve()
    process = subprocess.Popen([
        args.browser, "--headless=new", "--disable-gpu", "--no-first-run",
        "--remote-debugging-port=9345", "--remote-debugging-address=127.0.0.1", "--remote-allow-origins=*",
        f"--user-data-dir={profile}", "--window-size=1600,1000", "about:blank",
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    conn = None
    local_http = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        for _ in range(50):
            if process.poll() is not None:
                raise RuntimeError(f"Chromium exited: {process.returncode}")
            try:
                targets = json.load(local_http.open("http://127.0.0.1:9345/json", timeout=1))
                target = next(t for t in targets if t["type"] == "page")
                break
            except Exception:
                time.sleep(0.2)
        else:
            raise RuntimeError("Chromium did not become ready")
        conn = websocket.create_connection(target["webSocketDebuggerUrl"].replace("localhost", "127.0.0.1"), timeout=30,
                                           http_no_proxy=["localhost", "127.0.0.1"])
        counter = 0
        def call(method, params=None):
            nonlocal counter
            counter += 1
            conn.send(json.dumps({"id": counter, "method": method, "params": params or {}}))
            while True:
                response = json.loads(conn.recv())
                if response.get("id") == counter:
                    if "error" in response:
                        raise RuntimeError(response["error"])
                    return response.get("result", {})
        call("Page.enable")
        call("Emulation.setDeviceMetricsOverride", {"width": 1600, "height": 1000, "deviceScaleFactor": 1, "mobile": False})
        call("Page.navigate", {"url": args.url})
        for _ in range(60):
            text = call("Runtime.evaluate", {"expression": "document.body.innerText", "returnByValue": True})["result"].get("value", "")
            if "experiment-1-batch1" in text:
                break
            time.sleep(0.5)
        Path("outputs/mlflow-dom.txt").write_text(text, encoding="utf-8")
        call("Runtime.evaluate", {"expression": "[...document.querySelectorAll('button')].find(b => b.innerText.trim() === 'Columns')?.click()"})
        time.sleep(0.5)
        call("Runtime.evaluate", {"expression": """(() => {
            const wanted = new Set(['accuracy','f1_score','learning_rate','max_depth','n_estimators']);
            for (const label of document.querySelectorAll('.du-bois-light-tree-node-content-wrapper[title]')) {
                const name = label.getAttribute('title');
                const checkbox = label.parentElement.querySelector('.du-bois-light-tree-checkbox');
                if (checkbox && checkbox.classList.contains('du-bois-light-tree-checkbox-checked') !== wanted.has(name)) checkbox.click();
            }
        })()"""})
        time.sleep(0.5)
        call("Runtime.evaluate", {"expression": "[...document.querySelectorAll('button')].find(b => b.innerText.trim() === 'Columns')?.click()"})
        time.sleep(0.3)
        call("Runtime.evaluate", {"expression": """(() => {
            const label = document.querySelector('[data-test-id="sort-header-f1_score"]');
            if (label) label.click();
        })()"""})
        time.sleep(0.3)
        text = call("Runtime.evaluate", {"expression": "document.body.innerText", "returnByValue": True})["result"]["value"]
        Path("outputs/mlflow-dom.txt").write_text(text, encoding="utf-8")
        screenshot = call("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": False})
        output = Path("nop-bai/anh-chup-man-hinh/01-mlflow-ui.png")
        output.write_bytes(base64.b64decode(screenshot["data"]))
        print(f"Actual MLflow UI captured at {args.url}: {output}")
    finally:
        if conn:
            try:
                call("Browser.close")
            except Exception:
                pass
            conn.close()
        process.terminate()


if __name__ == "__main__":
    main()
