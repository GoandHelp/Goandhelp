"""Capture screenshots from an already-running Reflex app.

Example: ``python -m app.scripts.capture_screenshots --route / --route /verify``.
The Reflex app must already be running. This helper never starts or stops the
app or frontend; it only connects to the configured public base URL.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import re
from pathlib import Path
from urllib.parse import urljoin

from playwright.async_api import Browser, async_playwright

CONCURRENCY = 1
BROWSER_ARGS = (
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
)
DEFAULT_VIEWPORT = {"width": 1280, "height": 720}
DEFAULT_BASE_URL = "http://127.0.0.1:3000"
logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default=os.environ.get("SCREENSHOT_BASE_URL", DEFAULT_BASE_URL),
    )
    parser.add_argument("--route", action="append", default=None)
    parser.add_argument("--output-dir", default="artifacts/screenshots")
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--navigation-timeout", type=float, default=30_000)
    parser.add_argument("--post-load-delay", type=float, default=0.0)
    parser.add_argument("--full-page", action="store_true")
    parser.add_argument("--strict", action="store_true")
    return parser


def normalize_url(base_url: str, route: str) -> str:
    return urljoin(
        base_url.rstrip("/") + "/",
        (route if route.startswith("/") else f"/{route}").lstrip("/"),
    )


def safe_output_filename(route: str, index: int) -> str:
    path = route.split("?", 1)[0].strip("/") or "root"
    path = re.sub(r"[^A-Za-z0-9._-]+", "-", path).strip("-._") or "root"
    return f"{index:03d}-{path}.png"


def resolve_executable(bundled_executable: str) -> str | None:
    configured = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
    for candidate in (
        configured,
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        bundled_executable,
    ):
        if candidate and Path(candidate).is_file():
            return candidate
    return None


async def capture(args: argparse.Namespace) -> tuple[int, int]:
    routes = args.route or ["/"]
    succeeded = failed = 0
    async with async_playwright() as playwright:
        executable = resolve_executable(playwright.chromium.executable_path)
        if executable is None:
            logger.warning(
                "Chromium executable not found; no screenshots captured"
            )
            return 0, len(routes)
        browser: Browser | None = None
        try:
            browser = await playwright.chromium.launch(
                headless=True,
                executable_path=executable,
                args=list(BROWSER_ARGS),
            )
            Path(args.output_dir).mkdir(parents=True, exist_ok=True)
            for index, route in enumerate(routes, start=1):
                context = None
                try:
                    context = await browser.new_context(
                        viewport={"width": args.width, "height": args.height},
                        service_workers="block",
                        reduced_motion="reduce",
                    )
                    try:
                        page = await context.new_page()
                        try:
                            page.set_default_navigation_timeout(
                                args.navigation_timeout
                            )
                            await page.goto(
                                normalize_url(args.base_url, route),
                                wait_until="networkidle",
                            )
                            if args.post_load_delay:
                                await page.wait_for_timeout(
                                    args.post_load_delay * 1000
                                )
                            await page.screenshot(
                                path=str(
                                    Path(args.output_dir)
                                    / safe_output_filename(route, index)
                                ),
                                full_page=args.full_page,
                            )
                            succeeded += 1
                        finally:
                            try:
                                await page.close()
                            except Exception as exc:
                                logging.exception("Unexpected error")
                                logger.debug(
                                    "Handled screenshot runner exception",
                                    exc_info=False,
                                )
                                logger.warning(
                                    "Page cleanup failed: %s: %s",
                                    type(exc).__name__,
                                    exc,
                                )
                    finally:
                        try:
                            await context.close()
                        except Exception as exc:
                            logging.exception("Unexpected error")
                            logger.warning(
                                "Context cleanup failed: %s: %s",
                                type(exc).__name__,
                                exc,
                            )
                except Exception as exc:
                    logging.exception("Unexpected error")
                    failed += 1
                    logger.warning(
                        "Route %s failed: %s: %s",
                        route,
                        type(exc).__name__,
                        exc,
                    )
        except Exception as exc:
            logging.exception("Unexpected error")
            logger.warning(
                "Browser launch/capture failed: %s: %s", type(exc).__name__, exc
            )
            failed += len(routes) - succeeded
        finally:
            if browser is not None:
                try:
                    await browser.close()
                except Exception as exc:
                    logging.exception("Unexpected error")
                    logger.warning(
                        "Browser cleanup failed: %s: %s",
                        type(exc).__name__,
                        exc,
                    )
    return succeeded, failed


async def async_main(args: argparse.Namespace) -> int:
    try:
        succeeded, failed = await capture(args)
    except Exception as exc:
        logging.exception("Unexpected error")
        logger.warning(
            "Screenshot runner failed: %s: %s", type(exc).__name__, exc
        )
        succeeded, failed = 0, len(args.route or ["/"])
    logger.info(
        "Screenshots complete for %s: %d succeeded, %d failed",
        args.base_url,
        succeeded,
        failed,
    )
    return 1 if args.strict and failed else 0


def main() -> int:
    args = build_parser().parse_args()
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        return asyncio.run(async_main(args))
    except Exception as exc:
        logging.exception("Unexpected error")
        logger.warning(
            "Screenshot runner stopped: %s: %s", type(exc).__name__, exc
        )
        return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
