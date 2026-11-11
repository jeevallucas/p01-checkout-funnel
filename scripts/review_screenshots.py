"""Capture every report page at phone, tablet, and laptop widths and run axe on each.

Usage: serve report/_site (for example `python -m http.server 4173 -d report/_site`), then
`uv run python scripts/review_screenshots.py <round> [--base-url URL]`. Screenshots go to
docs/screenshots/review/<round>/ (git-ignored) and an axe summary is printed per page.
"""

import argparse
from pathlib import Path

from axe_playwright_python.sync_playwright import Axe
from playwright.sync_api import Page, sync_playwright

PAGES = ["index", "memo", "funnel", "repeat-purchase", "revenue", "method"]
VIEWPORTS = {"375": (375, 812), "768": (768, 1024), "1440": (1440, 900)}
REVIEW_DIR = Path(__file__).resolve().parents[1] / "docs" / "screenshots" / "review"


def wait_for_charts(page: Page) -> None:
    # OJS cells render after the CSV files load; wait until no cell is still pending.
    page.wait_for_load_state("networkidle")
    page.wait_for_function("document.querySelectorAll('.observablehq--running').length === 0")
    page.wait_for_timeout(300)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("round", help="name of the review round, used as the folder name")
    parser.add_argument("--base-url", default="http://127.0.0.1:4173")
    args = parser.parse_args()
    out_dir = REVIEW_DIR / args.round
    out_dir.mkdir(parents=True, exist_ok=True)
    axe = Axe()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for width_name, (width, height) in VIEWPORTS.items():
            page = browser.new_page(viewport={"width": width, "height": height})
            for name in PAGES:
                page.goto(f"{args.base_url}/{name}.html")
                wait_for_charts(page)
                page.screenshot(path=out_dir / f"{name}-{width_name}.png", full_page=True)
                overflow = page.evaluate(
                    "document.documentElement.scrollWidth > document.documentElement.clientWidth"
                )
                violations = axe.run(page).response["violations"]
                summary = ", ".join(f"{v['id']} ({len(v['nodes'])})" for v in violations)
                print(
                    f"{name} @ {width_name}: axe {len(violations)} violations"
                    f"{': ' + summary if summary else ''}; sideways scroll: {overflow}"
                )
            page.close()

        # Error state: the data files fail to load.
        page = browser.new_page(viewport={"width": 375, "height": 812})
        page.route("**/sources/results/*.csv", lambda route: route.abort())
        page.goto(f"{args.base_url}/funnel.html")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(500)
        page.screenshot(path=out_dir / "funnel-error-375.png", full_page=True)
        browser.close()
    print(f"Screenshots in {out_dir}")


if __name__ == "__main__":
    main()
