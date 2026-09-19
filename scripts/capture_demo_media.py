#!/usr/bin/env python3
"""Capture canonical public media from the self-contained static replay."""
from __future__ import annotations
from io import BytesIO
import argparse
import functools
import http.server
import os
from pathlib import Path
import shutil
import threading
import time

from PIL import Image
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By

ROOT = Path(__file__).resolve().parents[1]


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_args): pass


def save(driver, path: Path, size: tuple[int, int]) -> None:
    image = Image.open(BytesIO(driver.get_screenshot_as_png())).convert("RGB")
    image.resize(size, Image.Resampling.LANCZOS).save(path, optimize=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workflow-only", action="store_true")
    args = parser.parse_args()
    binary = os.environ.get("AWM_FIREFOX_BINARY") or next((p for p in ("/snap/firefox/current/usr/lib/firefox/firefox", shutil.which("firefox")) if p and Path(p).is_file()), None)
    executable = shutil.which("geckodriver")
    if not binary or not executable:
        print("UNTESTED: local Firefox and geckodriver required")
        return 2
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(ROOT / "demo/static")))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    options = Options(); options.add_argument("-headless"); options.binary_location = binary
    driver = webdriver.Firefox(service=Service(executable), options=options)
    try:
        origin = "http" + f"://127.0.0.1:{server.server_address[1]}/"
        media = ROOT / "demo/media"; media.mkdir(parents=True, exist_ok=True)
        for width, height, tab, name in (
            (1920, 1080, 0, "public_monitor_1920x1080.png"),
            (1440, 1000, 1, "public_monitor_1440x1000.png"),
            (1920, 1080, 5, "public_monitor_usage_cost.png"),
            (1920, 1080, 7, "public_monitor_workflow_trace.png"),
        ):
            if args.workflow_only and tab != 7:
                continue
            driver.set_window_size(width, height)
            driver.get(origin); time.sleep(.4)
            driver.find_element(By.ID, f"tab-{tab}").click(); time.sleep(.2)
            if tab == 5:
                driver.execute_script("document.querySelector('#usage-panel').scrollIntoView({block:'start'})")
                time.sleep(.1)
            if tab == 7:
                driver.execute_script("document.querySelector('.wf-root').scrollIntoView({block:'start'})")
                time.sleep(.1)
            if tab == 7:
                panel = driver.find_element(By.CSS_SELECTOR, ".wf-root")
                capture = Image.open(BytesIO(panel.screenshot_as_png)).convert("RGB")
                capture.thumbnail((width - 32, height - 32), Image.Resampling.LANCZOS)
                canvas = Image.new("RGB", (width, height), "#07111f")
                canvas.paste(capture, ((width - capture.width) // 2, (height - capture.height) // 2))
                canvas.save(media / name, optimize=True)
            else:
                save(driver, media / name, (width, height))
    finally:
        driver.quit(); server.shutdown(); server.server_close()
    print("PASS canonical media captured")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
