#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Phase D real-application benchmarks for Computer Use Lite.

Measures discover_interactables() across:
  - Browser fixture (labeled 'fixture')
  - 3+ heavy real web pages (GitHub, YouTube, Gmail) + Google Maps (canvas case)
  - Desktop real apps (Notepad, File Explorer, Chromium/Electron with/without a11y activation)

Reports BOTH default capped line_map(max_elements=60) tokens and uncapped line_map tokens
against the 1280x720 screenshot baseline (~1229 tokens). Never fakes or omits numbers.
"""
import ctypes
from ctypes import wintypes
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from computer_use_lite import Api, BrowserSession, DesktopSession, desktop_uia  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

SHOT_TOKENS = 1229  # 1280x720 viewport screenshot baseline
FORM = (ROOT / "tests" / "fixtures" / "form.html").as_uri()

BROWSER_TARGETS = [
    ("fixture", FORM, "fixture"),
    ("GitHub Trending", "https://github.com/trending", "real"),
    ("YouTube", "https://www.youtube.com", "real"),
    ("Gmail", "https://mail.google.com", "real"),
    ("Google Maps", "https://www.google.com/maps/@40.7580,-73.9855,17z", "real_canvas"),
]


def _windows_by_class(class_name):
    out = set()

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(hwnd, _):
        if desktop_uia._u32.IsWindowVisible(hwnd):
            buf = ctypes.create_unicode_buffer(256)
            desktop_uia._u32.GetClassNameW(hwnd, buf, 256)
            if buf.value == class_name:
                out.add(hwnd)
        return True

    desktop_uia._u32.EnumWindows(cb, 0)
    return out


def bench_browser():
    rows = []
    for label, url, kind in BROWSER_TARGETS:
        s = None
        try:
            s = BrowserSession(url=url, headless=True, viewport=(1280, 720))
            if kind == "real_canvas":
                s.page.wait_for_timeout(2000)
            elif kind == "real":
                s.page.wait_for_timeout(1200)
            api = Api(s, state_path=ROOT / "results" / "runtime" / "bench_state.json",
                      crops_dir=ROOT / "results" / "crops_bench")
            capped_map = api.discover_interactables(export_crops=(kind == "real_canvas"), max_elements=60)
            stats = dict(api.last_stats)
            uncapped_map = api.line_map(max_elements=None)
            uncapped_tokens = round(len(uncapped_map) / 4, 1)
            safe_url = "tests/fixtures/form.html" if kind == "fixture" else s.page.url
            rows.append({
                "label": label,
                "kind": kind,
                "url": safe_url,
                "elements": stats["elements"],
                "blind_regions": stats["blind_regions"],
                "latency_ms": stats["latency_ms"],
                "tokens_capped": stats["tokens"],
                "vs_shot_capped": round(stats["tokens"] / SHOT_TOKENS, 2),
                "tokens_uncapped": uncapped_tokens,
                "vs_shot_uncapped": round(uncapped_tokens / SHOT_TOKENS, 2),
            })
        except Exception as exc:
            rows.append({"label": label, "kind": kind, "url": url, "error": f"{type(exc).__name__}: {exc}"})
        finally:
            if s is not None:
                s.close()
    return rows


def _launch_notepad():
    tmp = Path(tempfile.gettempdir()) / f"cul_bench_{int(time.time())}.txt"
    tmp.write_text("", encoding="utf-8")
    before = _windows_by_class("Notepad")
    proc = subprocess.Popen(["notepad.exe", str(tmp)])
    hwnd = None
    for _ in range(30):
        diff = _windows_by_class("Notepad") - before
        if diff:
            hwnd = next(iter(diff))
            break
        time.sleep(0.3)
    return hwnd, proc, tmp


def bench_desktop():
    rows = []

    # 1. Notepad
    hwnd, proc, tmp = _launch_notepad()
    try:
        if hwnd:
            time.sleep(0.6)
            s = DesktopSession(hwnd)
            api = Api(s, state_path=ROOT / "results" / "runtime" / "bench_state.json")
            api.discover_interactables(export_crops=False, max_elements=60)
            uncapped = round(len(api.line_map(max_elements=None)) / 4, 1)
            st = api.last_stats
            rows.append({
                "label": "Notepad (Win11)",
                "elements": st["elements"],
                "blind_regions": st["blind_regions"],
                "latency_ms": st["latency_ms"],
                "tokens_capped": st["tokens"],
                "vs_shot_capped": round(st["tokens"] / SHOT_TOKENS, 2),
                "tokens_uncapped": uncapped,
                "vs_shot_uncapped": round(uncapped / SHOT_TOKENS, 2),
            })
            desktop_uia._u32.PostMessageW(hwnd, 0x0010, 0, 0)
            time.sleep(0.4)
    finally:
        tmp.unlink(missing_ok=True)

    # 2. File Explorer
    before_exp = _windows_by_class("CabinetWClass")
    subprocess.Popen(["explorer.exe", str(ROOT)])
    exp_hwnd = None
    for _ in range(25):
        diff = _windows_by_class("CabinetWClass") - before_exp
        if diff:
            exp_hwnd = next(iter(diff))
            break
        time.sleep(0.3)
    if exp_hwnd:
        time.sleep(1.0)
        s = DesktopSession(exp_hwnd)
        api = Api(s, state_path=ROOT / "results" / "runtime" / "bench_state.json")
        api.discover_interactables(export_crops=False, max_elements=60)
        uncapped = round(len(api.line_map(max_elements=None)) / 4, 1)
        st = api.last_stats
        rows.append({
            "label": "File Explorer",
            "elements": st["elements"],
            "blind_regions": st["blind_regions"],
            "latency_ms": st["latency_ms"],
            "tokens_capped": st["tokens"],
            "vs_shot_capped": round(st["tokens"] / SHOT_TOKENS, 2),
            "tokens_uncapped": uncapped,
            "vs_shot_uncapped": round(uncapped / SHOT_TOKENS, 2),
        })
        desktop_uia._u32.PostMessageW(exp_hwnd, 0x0010, 0, 0)
        time.sleep(0.4)

    # 3. Chromium/Electron without vs with accessibility activation
    sample_html = (
        "<!doctype html><html><body>"
        "<h1>App Shell</h1>"
        "<input aria-label='Search' placeholder='Search'><button>Run</button>"
        "<button>Save</button><a href='#'>Docs</a><input type='checkbox' aria-label='Auto'>"
        "</body></html>"
    )
    for forced in (False, True):
        before_ch = _windows_by_class("Chrome_WidgetWin_1")
        args = ["--window-position=20,20", "--window-size=900,600"]
        if forced:
            args.append("--force-renderer-accessibility")
        with sync_playwright() as p:
            b = p.chromium.launch(headless=False, args=args)
            pg = b.new_page()
            pg.set_content(sample_html)
            pg.wait_for_timeout(400)
            ch_hwnd = next(iter(_windows_by_class("Chrome_WidgetWin_1") - before_ch))
            s = DesktopSession(ch_hwnd)
            if not forced:
                # Measure pre-activation scan directly, then DesktopSession.discover() with WM_GETOBJECT
                pre_nodes = s._call(s._scan)
                pre_inter = sum(1 for n in pre_nodes if n["role"] in desktop_uia.INTERACTIVE)
                api = Api(s, state_path=ROOT / "results" / "runtime" / "bench_state.json")
                api.discover_interactables(export_crops=False, max_elements=60)
                st = api.last_stats
                uncapped = round(len(api.line_map(max_elements=None)) / 4, 1)
                rows.append({
                    "label": "Chromium shell (before a11y trigger)",
                    "elements": pre_inter,
                    "blind_regions": "-",
                    "latency_ms": "-",
                    "tokens_capped": "-",
                    "vs_shot_capped": "-",
                    "tokens_uncapped": "-",
                    "vs_shot_uncapped": "-",
                    "note": f"raw interactive={pre_inter}, total={len(pre_nodes)} (renderer inert)",
                })
                rows.append({
                    "label": "Chromium shell (after B13 WM_GETOBJECT)",
                    "elements": st["elements"],
                    "blind_regions": st["blind_regions"],
                    "latency_ms": st["latency_ms"],
                    "tokens_capped": st["tokens"],
                    "vs_shot_capped": round(st["tokens"] / SHOT_TOKENS, 2),
                    "tokens_uncapped": uncapped,
                    "vs_shot_uncapped": round(uncapped / SHOT_TOKENS, 2),
                })
            else:
                api = Api(s, state_path=ROOT / "results" / "runtime" / "bench_state.json")
                api.discover_interactables(export_crops=False, max_elements=60)
                st = api.last_stats
                uncapped = round(len(api.line_map(max_elements=None)) / 4, 1)
                rows.append({
                    "label": "Chromium shell (--force-renderer-accessibility)",
                    "elements": st["elements"],
                    "blind_regions": st["blind_regions"],
                    "latency_ms": st["latency_ms"],
                    "tokens_capped": st["tokens"],
                    "vs_shot_capped": round(st["tokens"] / SHOT_TOKENS, 2),
                    "tokens_uncapped": uncapped,
                    "vs_shot_uncapped": round(uncapped / SHOT_TOKENS, 2),
                })
            b.close()

    return rows


def main():
    out = ROOT / "results" / "benchmarks"
    out.mkdir(parents=True, exist_ok=True)
    browser_rows = bench_browser()
    desktop_rows = bench_desktop()
    data = {"shot_tokens": SHOT_TOKENS, "browser": browser_rows, "desktop": desktop_rows}
    (out / "benchmarks_real.json").write_text(json.dumps(data, indent=2), encoding="utf-8")

    b_lines = "\n".join(
        f"| {r['label']} ({r['kind']}) | {r.get('elements', '-')} | {r.get('blind_regions', '-')} "
        f"| {r.get('latency_ms', '-')} ms | {r.get('tokens_capped', '-')} ({r.get('vs_shot_capped', '-')}x) "
        f"| {r.get('tokens_uncapped', '-')} ({r.get('vs_shot_uncapped', '-')}x) |"
        if "error" not in r else f"| {r['label']} ({r['kind']}) | ERROR | - | - | {r['error']} | - |"
        for r in browser_rows
    )
    d_lines = "\n".join(
        f"| {r['label']} | {r['elements']} | {r['blind_regions']} | {r['latency_ms']} "
        f"| {r['tokens_capped']} ({r['vs_shot_capped']}x) | {r['tokens_uncapped']} ({r['vs_shot_uncapped']}x) |"
        for r in desktop_rows
    )
    md = f"""# Real-Application Benchmarks (Phase D)

Baseline 1280x720 screenshot: **{SHOT_TOKENS} tokens**.

## Browser targets

| target | elements | blind regions | latency | capped line_map (<=60) | uncapped line_map |
| --- | --- | --- | --- | --- | --- |
{b_lines}

## Windows desktop targets

| target | elements | blind regions | latency (ms) | capped line_map (<=60) | uncapped line_map |
| --- | --- | --- | --- | --- | --- |
{d_lines}
"""
    (out / "benchmarks_real.md").write_text(md, encoding="utf-8")
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
