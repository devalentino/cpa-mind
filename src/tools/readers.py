from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlencode

from bs4 import BeautifulSoup
from markdownify import markdownify as html_to_markdown
from playwright.sync_api import sync_playwright


@dataclass(slots=True)
class FacebookAdsLibraryReader:
    def run(self, search_term: str, country: str) -> str:
        ads_library_url = self._build_ads_library_url(search_term, country)

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=False)
            page = browser.new_page()

            try:
                page.goto(ads_library_url, wait_until="domcontentloaded")
                page.wait_for_load_state("networkidle")
                search_results_markdown = self._page_to_markdown(page.content())
            finally:
                browser.close()

        return search_results_markdown

    def _build_ads_library_url(self, search_term: str, country: str) -> str:
        query = urlencode(
            {
                "active_status": "active",
                "ad_type": "all",
                "country": country,
                "is_targeted_country": "false",
                "media_type": "all",
                "q": f'"{search_term}"',
                "search_type": "keyword_exact_phrase",
                "sort_data[direction]": "desc",
                "sort_data[mode]": "total_impressions",
            }
        )
        return f"https://www.facebook.com/ads/library/?{query}"

    def _page_to_markdown(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        page_root = soup.body or soup

        for tag_name in ("script", "style", "noscript", "svg", "canvas"):
            for tag in page_root.find_all(tag_name):
                tag.decompose()

        for tag in page_root.find_all(attrs={"aria-hidden": "true"}):
            tag.decompose()

        cleaned_html = str(page_root)
        markdown = html_to_markdown(
            cleaned_html,
            heading_style="ATX",
            bullets="-",
            strip=["img"],
        )
        lines = [line.rstrip() for line in markdown.splitlines()]
        non_empty_lines = [line for line in lines if line.strip()]
        return "\n".join(non_empty_lines).strip()


@dataclass(slots=True)
class GoogleTrendsReader:
    def run(self, offer_url: str) -> dict[str, str]:
        return {
            "offer_url": offer_url,
            "trend_summary": "TODO: implement Google Trends API lookup.",
            "interest_over_time": "TODO: implement time-series trend retrieval.",
        }
