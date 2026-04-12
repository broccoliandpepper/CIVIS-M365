#!/usr/bin/env python3
"""Basic Playwright E2E test for SIEM M365 V2 UI."""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


@dataclass
class TestResult:
    name: str
    ok: bool
    details: str = ""


def env_or_default(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value else default


def run_test(base_url: str, username: str, password: str, headed: bool) -> list[TestResult]:
    results: list[TestResult] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not headed)
        context = browser.new_context()
        page = context.new_page()

        try:
            page.goto(base_url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_selector("#login-form", timeout=10000)
            results.append(TestResult("Open login page", True))
        except PlaywrightTimeoutError:
            results.append(TestResult("Open login page", False, "Login form not visible"))
            browser.close()
            return results

        try:
            page.fill('input[name="username"]', username)
            page.fill('input[name="password"]', password)
            page.click('#login-form button[type="submit"]')
            page.wait_for_selector("#navbar", timeout=15000)
            page.wait_for_selector("#content", timeout=10000)
            results.append(TestResult("Login", True))
        except PlaywrightTimeoutError:
            results.append(TestResult("Login", False, "Navbar/content not visible after submit"))
            browser.close()
            return results

        try:
            dashboard_btn = page.locator('.nav-btn[data-view="dashboard"]')
            dashboard_btn.click()
            page.wait_for_selector("text=Dashboard", timeout=10000)
            results.append(TestResult("Navigate dashboard", True))
        except PlaywrightTimeoutError:
            results.append(TestResult("Navigate dashboard", False, "Dashboard view not rendered"))

        try:
            soc_btn = page.locator('.nav-btn[data-view="soc"]')
            soc_btn.click()
            page.wait_for_selector("#soc-run-analysis", timeout=10000)
            page.click("#soc-run-analysis")
            page.wait_for_timeout(1200)
            results.append(TestResult("SOC view action", True))
        except PlaywrightTimeoutError:
            results.append(TestResult("SOC view action", False, "SOC controls not reachable"))

        lifecycle_btn = page.locator('.nav-btn[data-view="lifecycle"]')
        if lifecycle_btn.count() > 0:
            try:
                lifecycle_btn.click()
                page.wait_for_selector("#refresh-lifecycle-btn", timeout=10000)
                page.click("#refresh-lifecycle-btn")
                page.wait_for_timeout(1000)
                results.append(TestResult("Lifecycle view action", True))
            except PlaywrightTimeoutError:
                results.append(TestResult("Lifecycle view action", False, "Lifecycle controls not reachable"))
        else:
            results.append(TestResult("Lifecycle view action", False, "Lifecycle tab not found (non-admin or UI issue)"))

        browser.close()

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Playwright E2E UI checks")
    parser.add_argument("--base-url", default=env_or_default("SIEM_BASE_URL", "http://127.0.0.1:5000/"))
    parser.add_argument("--username", default=env_or_default("SIEM_E2E_USERNAME", "admin"))
    parser.add_argument("--password", default=env_or_default("SIEM_E2E_PASSWORD", "Admin@SIEM2024!"))
    parser.add_argument("--headed", action="store_true", help="Run browser in headed mode")
    args = parser.parse_args()

    results = run_test(args.base_url, args.username, args.password, args.headed)

    print("E2E UI RESULTS")
    failed = 0
    for item in results:
        status = "OK" if item.ok else "FAIL"
        print(f"- [{status}] {item.name}{': ' + item.details if item.details else ''}")
        if not item.ok:
            failed += 1

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
