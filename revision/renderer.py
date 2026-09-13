from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright


class BrowserRenderer:
    def __init__(self, viewport: tuple[int, int] = (1440, 900)) -> None:
        self.viewport = viewport

    def capture(self, html_path: Path, output_path: Path) -> Path:
        html_path = html_path.resolve()
        output_path = output_path.resolve()

        if not html_path.exists():
            raise FileNotFoundError(f"HTML file does not exist: {html_path}")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(
                viewport={
                    "width": self.viewport[0],
                    "height": self.viewport[1],
                }
            )
            page.goto(html_path.as_uri(), wait_until="networkidle")
            page.screenshot(path=str(output_path), full_page=False)
            browser.close()

        return output_path

