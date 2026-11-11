"""Record the main reading path through the report as an animated GIF for the README.

Usage: serve report/_site on port 4173, then `uv run python scripts/record_demo.py`.
The path: the overview's step ladder, the memo's first recommendation, the mobile gap chart,
and the revenue comparison. Frames are screenshots, so the GIF shows exactly what renders.
"""

from io import BytesIO
from pathlib import Path

from PIL import Image
from playwright.sync_api import Page, sync_playwright

BASE_URL = "http://127.0.0.1:4173"
OUTPUT = Path(__file__).resolve().parents[1] / "docs" / "screenshots" / "demo.gif"
VIEWPORT = {"width": 1280, "height": 760}
GIF_WIDTH = 960


def frame(page: Page) -> Image.Image:
    shot = Image.open(BytesIO(page.screenshot()))
    height = round(shot.height * GIF_WIDTH / shot.width)
    return shot.resize((GIF_WIDTH, height), Image.Resampling.LANCZOS).convert("RGB")


def settle(page: Page) -> None:
    page.wait_for_load_state("networkidle")
    page.wait_for_function("document.querySelectorAll('.observablehq--running').length === 0")
    page.wait_for_timeout(400)


def scroll_frames(page: Page, distance: int, steps: int) -> list[Image.Image]:
    frames = []
    for _ in range(steps):
        page.mouse.wheel(0, distance / steps)
        page.wait_for_timeout(120)
        frames.append(frame(page))
    return frames


def main() -> None:
    frames: list[tuple[Image.Image, int]] = []  # (image, milliseconds on screen)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT)

        page.goto(f"{BASE_URL}/index.html")
        settle(page)
        frames.append((frame(page), 2200))
        frames += [(image, 90) for image in scroll_frames(page, 330, 6)]
        frames.append((frame(page), 3000))

        page.goto(f"{BASE_URL}/memo.html")
        settle(page)
        frames.append((frame(page), 1400))
        page.get_by_role("heading", name="Recommendation 1").scroll_into_view_if_needed()
        page.wait_for_timeout(200)
        frames.append((frame(page), 3000))

        page.goto(f"{BASE_URL}/funnel.html")
        settle(page)
        frames.append((frame(page), 1200))
        frames += [(image, 90) for image in scroll_frames(page, 360, 6)]
        frames.append((frame(page), 3000))

        page.goto(f"{BASE_URL}/revenue.html")
        settle(page)
        frames.append((frame(page), 1200))
        frames += [(image, 90) for image in scroll_frames(page, 260, 5)]
        frames.append((frame(page), 3200))
        browser.close()

    images = [image.quantize(colors=128, method=Image.Quantize.MEDIANCUT) for image, _ in frames]
    images[0].save(
        OUTPUT,
        save_all=True,
        append_images=images[1:],
        duration=[duration for _, duration in frames],
        loop=0,
        optimize=True,
    )
    print(f"{OUTPUT}: {len(images)} frames, {OUTPUT.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
