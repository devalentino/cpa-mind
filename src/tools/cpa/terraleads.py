from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from markdownify import markdownify as html_to_markdown
from playwright.sync_api import Browser
from playwright.sync_api import BrowserContext
from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from tools.cpa.base import OfferParserStrategy


class TerraleadsOfferParserStrategy(OfferParserStrategy):
    platform_name = "terraleads"
    state_file_name = "terraleads_playwrite_state.json"

    def __init__(
        self,
        login: str,
        password: str,
        cache_path: str | None = None,
    ) -> None:
        self._login = login
        self._password = password
        self._cache_dir = Path(cache_path).expanduser() if cache_path else None

    def supports(self, offer_url: str) -> bool:
        hostname = urlparse(offer_url).netloc.lower()
        return "terraleads" in hostname

    def parse_offer(self, offer_url: str) -> str:
        self._validate_credentials()

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=False)
            browser_context = self._new_browser_context(browser)
            page = browser_context.new_page()

            try:
                page.goto(offer_url, wait_until="domcontentloaded")
                page.wait_for_load_state("networkidle")

                if self._is_unauthenticated_index_page(page):
                    self._authenticate(page)
                    self._save_playwright_storage_state(browser_context)

                offer_markdown = self._parse_offer_page(page, offer_url)
            finally:
                browser.close()

        return offer_markdown

    def _new_browser_context(self, browser: Browser) -> BrowserContext:
        state_file = self._playwright_state_file_path()
        if state_file and state_file.exists():
            return browser.new_context(storage_state=str(state_file))
        return browser.new_context()

    def _validate_credentials(self) -> None:
        if not self._login or not self._password:
            raise RuntimeError("Terraleads credentials are required for authentication.")

    def _authenticate(self, page: Page) -> None:
        login_url = "https://terraleads.com/login"
        page.goto(login_url, wait_until="domcontentloaded")
        login_form = page.locator('form.auth__form[action="/acp/startup/login"]')
        login_form.locator('input[name="email"]').fill(self._login)
        login_form.locator('input[name="password"]').fill(self._password)
        login_form.locator('button[name="submit"]').click()
        # input("Please solve reCAPTCHA, then press Enter to continue...")
        page.wait_for_load_state("networkidle")
        self._wait_for_authenticated_page(page)

    def _save_playwright_storage_state(self, browser_context: BrowserContext) -> None:
        state_file = self._playwright_state_file_path()
        if not state_file:
            return

        state_file.parent.mkdir(parents=True, exist_ok=True)
        browser_context.storage_state(path=str(state_file))

    def _playwright_state_file_path(self) -> Path | None:
        if not self._cache_dir:
            return None
        return self._cache_dir / self.state_file_name

    def _is_unauthenticated_index_page(self, page: Page) -> bool:
        return page.locator('a.promo__btn[href="/registration"]').count() > 0

    def _wait_for_authenticated_page(self, page: Page) -> None:
        expected_url = "https://terraleads.com/acp/dashboard/welcome"

        try:
            page.wait_for_url(expected_url, timeout=15_000)
            return
        except PlaywrightTimeoutError:
            pass

        raise RuntimeError(
            "Terraleads login did not complete successfully. "
            f"Expected redirect to {expected_url}, got {page.url}."
        )

    def _parse_offer_page(
        self,
        page: Page,
        offer_url: str,
    ) -> str:
        if page.url != offer_url:
            page.goto(offer_url, wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle")
        raw_html = page.content()
        cleaned_html = self._extract_offer_wrap_html(raw_html)
        offer_markdown = self._html_to_markdown(cleaned_html)
        title = page.title().strip()
        return (
            f"# {title}\n\n"
            f"Source URL: {offer_url}\n\n"
            f"{offer_markdown}"
        ).strip()

    def _extract_offer_wrap_html(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        offer_wrap = soup.select_one("div.offer-wrap")
        if offer_wrap is None:
            raise RuntimeError("Terraleads offer page does not contain div.offer-wrap.")

        for tag_name in ("script", "style", "iframe", "noscript", "svg", "canvas"):
            for tag in offer_wrap.find_all(tag_name):
                tag.decompose()

        for tag in offer_wrap.find_all(attrs={"aria-hidden": "true"}):
            tag.decompose()

        for tag in offer_wrap.find_all(hidden=True):
            tag.decompose()

        for tag in offer_wrap.find_all(style=True):
            style_value = tag.get("style", "").replace(" ", "").lower()
            if "display:none" in style_value or "visibility:hidden" in style_value:
                tag.decompose()

        return str(offer_wrap)

    def _html_to_markdown(self, html: str) -> str:
        markdown = html_to_markdown(
            html,
            heading_style="ATX",
            bullets="-",
            strip=["img"],
        )
        lines = [line.rstrip() for line in markdown.splitlines()]
        non_empty_lines = [line for line in lines if line.strip()]
        return "\n".join(non_empty_lines).strip()
