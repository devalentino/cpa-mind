from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from bs4 import BeautifulSoup
from markdownify import markdownify as html_to_markdown
from playwright.sync_api import Page
from playwright.sync_api import sync_playwright


@dataclass(slots=True)
class ParsedOffer:
    offer: str
    landing_urls: list[str]
    prelanding_urls: list[str]


@dataclass(slots=True)
class LandingReader:
    def parse(self, url: str) -> str:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=False)
            page = browser.new_page()

            try:
                page.goto(url, wait_until="domcontentloaded")
                page.wait_for_load_state("networkidle")
                body_html = self._extract_page_body_html(page)
            finally:
                browser.close()

        markdown = self._html_to_markdown(body_html)
        return markdown

    def _extract_page_body_html(self, page: Page) -> str:
        soup = BeautifulSoup(page.content(), "html.parser")
        page_root = soup.body or soup

        for selector in (
            "header",
            "footer",
            "nav",
            "aside",
            "script",
            "style",
            "noscript",
            "svg",
            "canvas",
        ):
            for tag in page_root.select(selector):
                tag.decompose()

        for tag in page_root.find_all(attrs={"aria-hidden": "true"}):
            tag.decompose()

        for tag in page_root.find_all(hidden=True):
            tag.decompose()

        for tag in page_root.find_all(True):
            if tag.attrs is None:
                continue

            classes = " ".join(tag.get("class", [])).lower()
            element_id = str(tag.get("id", "")).lower()
            if any(
                token in f"{classes} {element_id}"
                for token in (
                    "header",
                    "footer",
                    "nav",
                    "menu",
                    "sidebar",
                    "popup",
                    "modal",
                    "cookie",
                )
            ):
                tag.decompose()

        return str(page_root)

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

class OfferParserStrategy(ABC):
    platform_name: str

    @abstractmethod
    def supports(self, offer_url: str) -> bool:
        pass

    @abstractmethod
    def parse_offer(self, offer_url: str) -> ParsedOffer:
        pass


class UnsupportedOfferParserStrategy(OfferParserStrategy):
    platform_name = "unsupported"

    def supports(self, offer_url: str) -> bool:
        return True

    def parse_offer(self, offer_url: str) -> ParsedOffer:
        return ParsedOffer(
            offer=(
                f"# Unsupported CPA Platform\n\n"
                f"Offer URL: {offer_url}\n\n"
                "TODO: implement offer parser for this CPA platform.\n\n"
                "- No platform-specific OfferReader strategy matched this URL.\n"
                "- Add a parser strategy for this CPA dashboard."
            ),
            landing_urls=[],
            prelanding_urls=[],
        )


@dataclass(slots=True)
class OfferReader:
    strategies: tuple[OfferParserStrategy, ...]
    landing_reader: LandingReader

    def run(self, offer_url: str) -> dict[str, Any]:
        strategy = self._select_strategy(offer_url)
        parsed_offer = strategy.parse_offer(offer_url)
        return {
            "offer": parsed_offer.offer,
            "landings": [self.landing_reader.parse(url) for url in parsed_offer.landing_urls],
            "prelandings": [
                self.landing_reader.parse(url) for url in parsed_offer.prelanding_urls
            ],
        }

    def _select_strategy(self, offer_url: str) -> OfferParserStrategy:
        for strategy in self.strategies:
            if strategy.supports(offer_url):
                return strategy
        raise RuntimeError(f"No OfferReader strategy available for URL: {offer_url}")
