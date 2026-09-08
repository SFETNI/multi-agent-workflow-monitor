#!/usr/bin/env python3
"""Audit the static and embedded product in an unrelated local directory."""
from __future__ import annotations

import argparse
import functools
import http.server
import json
import os
import shutil
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from agent_workflow_monitor.presentation import render_overview_html
from agent_workflow_monitor.schema import load_config, load_snapshot


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args): pass


def browser(binary, driver, reduced=False):
    from selenium import webdriver
    from selenium.webdriver.firefox.options import Options
    from selenium.webdriver.firefox.service import Service
    options = Options(); options.add_argument("-headless"); options.binary_location = binary
    options.set_preference("ui.prefersReducedMotion", int(reduced))
    result = webdriver.Firefox(service=Service(driver), options=options)
    result.set_page_load_timeout(20)
    return result


def geometry(driver):
    return driver.execute_script("""
      return Object.fromEntries([...document.querySelectorAll('#view-1 .av-node, #view-1 .av-root, #view-1 .ap-activity, #view-1 .ap-context-card')].map((n,i)=>{
        const r=n.getBoundingClientRect();return [n.dataset.node||'part-'+i,[r.x,r.y,r.width,r.height]];
      }));
    """)


def audit(binary: str, executable: str, reference: Path | None = None) -> dict:
    from selenium.webdriver.common.by import By
    checks = {}
    with tempfile.TemporaryDirectory(prefix="awm-browser-v2-") as directory:
        root = Path(directory)
        shutil.copytree(ROOT / "demo/static", root / "static")
        snapshot = load_snapshot(ROOT / "demo/public_snapshot.json")
        config = load_config(ROOT / "config/example.yaml")
        (root / "runtime.html").write_text(render_overview_html(snapshot, config), encoding="utf-8")
        if reference:
            target = root / "reference"; (target / "data").mkdir(parents=True)
            for name in ("index.html", "app.js", "geometry.js", "presentation.js", "presentation.css", "shell.css", "data/public_snapshot.js"):
                shutil.copyfile(reference / name, target / name)
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(QuietHandler, directory=str(root)))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        origin = "http" + f"://127.0.0.1:{server.server_address[1]}/"
        driver = None
        try:
            driver = browser(binary, executable)
            for width, height in ((1920, 1080), (1440, 1000)):
                driver.set_window_size(width, height)
                sizes = {}
                for route in (["static/index.html", "runtime.html", "reference/index.html"] if reference else ["static/index.html", "runtime.html"]):
                    driver.get(origin + route); time.sleep(.25)
                    assert not driver.find_element(By.ID, "safe-error").is_displayed()
                    assert len(driver.find_elements(By.CSS_SELECTOR, "[role=tab]")) == 7
                    assert len(driver.find_elements(By.CSS_SELECTOR, "#view-1 .ap-context-card")) == 5
                    assert len(driver.find_elements(By.CSS_SELECTOR, "#view-1 .hs-item")) == 8
                    sizes[route] = geometry(driver)
                primary = sizes["static/index.html"]
                for route, values in sizes.items():
                    assert primary.keys() == values.keys()
                    assert max(abs(a-b) for key in primary for a,b in zip(primary[key], values[key])) < .15, route
                checks[f"geometry_{width}"] = True
            driver.get(origin + "static/index.html"); time.sleep(.15)
            for i in range(7):
                driver.find_element(By.ID, f"tab-{i}").click()
                assert driver.find_element(By.ID, f"view-{i}").is_displayed()
            checks["seven_views"] = True
            driver.find_element(By.ID, "tab-1").click()
            driver.find_element(By.ID, "fit").click(); time.sleep(.1)
            assert driver.execute_script("return getComputedStyle(document.querySelector('.av-root')).height") == "866px"
            driver.find_element(By.ID, "fit").click()
            driver.find_element(By.ID, "full").click()
            assert "fullscreen" in driver.find_element(By.TAG_NAME, "body").get_attribute("class")
            driver.execute_script("document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape'}))")
            assert "fullscreen" not in driver.find_element(By.TAG_NAME, "body").get_attribute("class")
            driver.execute_script("const n=document.querySelector('#filter');n.value='Workstream-01';n.dispatchEvent(new Event('change'))")
            assert driver.find_elements(By.CSS_SELECTOR, ".av-dim")
            driver.execute_script("const n=document.querySelector('#filter');n.value='both';n.dispatchEvent(new Event('change'))")
            driver.find_element(By.ID, "handoffs").click()
            assert not driver.find_element(By.CSS_SELECTOR, ".av-edge-capsule").is_displayed()
            driver.find_element(By.ID, "handoffs").click()
            checks["map_controls"] = True
            angle = lambda: float(driver.find_element(By.CSS_SELECTOR, ".av-beam-rotor").get_attribute("data-angle"))
            arc = lambda: driver.execute_script("return getComputedStyle(document.querySelector('.av-activity-arc')).transform")
            before, ring = angle(), arc(); time.sleep(.6)
            assert angle() > before and arc() != ring
            driver.find_element(By.ID, "motion").click(); time.sleep(.1)
            before, ring = angle(), arc(); time.sleep(.3)
            assert angle() == before and arc() == ring
            driver.find_element(By.ID, "motion").click(); time.sleep(.3)
            assert angle() > before
            checks["motion_pause_resume"] = True
            driver.find_element(By.CSS_SELECTOR, '#view-1 [data-session="A-02"]').click()
            assert driver.find_element(By.ID, "view-2").is_displayed()
            checks["session_inspector"] = True
            assert not driver.get_cookies()
            assert driver.execute_script("return [Object.keys(localStorage),Object.keys(sessionStorage)]") == [[], []]
            assert not driver.find_elements(By.TAG_NAME, "iframe")
            resources = driver.execute_script("return performance.getEntriesByType('resource').map(e=>e.name)")
            assert all(url.startswith(origin) for url in resources)
            checks["same_origin_empty_storage_cookies_frames"] = True
            driver.quit(); driver = browser(binary, executable, reduced=True)
            driver.get(origin + "runtime.html"); time.sleep(.2)
            assert not driver.find_element(By.ID, "motion").is_selected()
            before = angle(); time.sleep(.3); assert angle() == before
            assert driver.execute_script("return getComputedStyle(document.querySelector('.av-activity-arc')).animationName") == "none"
            checks["reduced_motion"] = True
            driver.find_element(By.ID, "motion").click(); time.sleep(.3)
            assert angle() > before
            checks["explicit_motion_override"] = True
        finally:
            if driver: driver.quit()
            server.shutdown(); server.server_close()
    return {"status": "PASS", "checks": checks, "reference_comparison": reference is not None}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--result", type=Path)
    args = parser.parse_args()
    binary = os.environ.get("AWM_FIREFOX_BINARY") or next((p for p in (str(Path("/") / "snap/firefox/current/usr/lib/firefox/firefox"), shutil.which("firefox")) if p and Path(p).is_file()), None)
    executable = shutil.which("geckodriver")
    if not binary or not executable:
        print("UNTESTED: local Firefox and geckodriver required")
        return 2
    result = audit(binary, executable, args.reference)
    encoded = json.dumps(result, indent=2) + "\n"
    if args.result: args.result.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
