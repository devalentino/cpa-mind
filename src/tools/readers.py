from __future__ import annotations

from dataclasses import dataclass
import re
from urllib.parse import parse_qs, urlencode, urlparse

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


@dataclass(slots=True)
class FacebookAdsLibraryReader:
    def run(self, search_term: str, country: str) -> list[dict]:
        ads_library_url = self._build_ads_library_url(search_term, country)

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=False)
            page = browser.new_page()

            try:
                page.goto(ads_library_url, wait_until="domcontentloaded")
                page.wait_for_load_state("networkidle")
                page.wait_for_selector(
                    '[data-testid="ad-library-ad-carousel-container"], '
                    '[data-testid="ad-library-dynamic-content-container"]',
                    timeout=15_000,
                )
                ads = self._parse_ads(page.content())
            finally:
                browser.close()

        return ads

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

    def _parse_ads(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        ad_sections = soup.select(
            '[data-testid="ad-library-ad-carousel-container"], '
            '[data-testid="ad-library-dynamic-content-container"]'
        )

        ad_cards = [self._extract_ad_card(section) for section in ad_sections]
        return [card for card in ad_cards if card]


    def _extract_ad_card(self, section: BeautifulSoup) -> dict[str, str | list[str]]:
        section_copy = BeautifulSoup(str(section), "html.parser")
        for tag_name in ("script", "style", "noscript", "svg", "canvas"):
            for tag in section_copy.find_all(tag_name):
                tag.decompose()

        for tag in section_copy.find_all(attrs={"aria-hidden": "true"}):
            tag.decompose()

        text_lines = self._visible_text_lines(section_copy)
        body_text = "\n".join(text_lines)

        library_id = self._extract_match(body_text, r"Ідентифікатор бібліотеки:\s*([0-9]+)")
        status = self._extract_first(text_lines, {"Активна", "Неактивна"})
        start_date = self._extract_match(body_text, r"Початок показу:\s*([^\n]+)")
        if not start_date:
            start_date = self._extract_date_range(text_lines)

        advertiser = self._extract_advertiser(section_copy)
        advertiser_profile_url = self._extract_advertiser_profile_url(section_copy)
        destination_urls = self._extract_destination_urls(section_copy)
        card_texts = self._extract_card_texts(section_copy)

        card: dict[str, str | list[str]] = {
            "library_id": library_id,
            "status": status,
            "start_date": start_date,
            "advertiser": advertiser,
            "advertiser_profile_url": advertiser_profile_url,
            "body": self._extract_body_text(text_lines),
            "card_texts": card_texts,
            "destination_urls": destination_urls,
        }
        return {key: value for key, value in card.items() if value}

    def _visible_text_lines(self, node: BeautifulSoup) -> list[str]:
        raw_lines = [line.strip() for line in node.get_text("\n").splitlines()]
        lines: list[str] = []
        for line in raw_lines:
            if not line or line == "\u200b":
                continue
            if line in {"Відкрити меню", "Переглянути деталі реклами", "See Details"}:
                continue
            if line not in lines:
                lines.append(line)
        return lines

    def _extract_match(self, text: str, pattern: str) -> str:
        match = re.search(pattern, text)
        return match.group(1).strip() if match else ""

    def _extract_first(self, lines: list[str], options: set[str]) -> str:
        for line in lines:
            if line in options:
                return line
        return ""

    def _extract_date_range(self, lines: list[str]) -> str:
        for line in lines:
            if " – " in line:
                return line
        return ""

    def _extract_advertiser(self, section: BeautifulSoup) -> str:
        for link in section.select('a[href^="https://www.facebook.com/"]'):
            text = " ".join(link.stripped_strings).strip()
            if text:
                return text
        return ""

    def _extract_advertiser_profile_url(self, section: BeautifulSoup) -> str:
        link = section.select_one('a[href^="https://www.facebook.com/"]')
        return str(link["href"]).strip() if link and link.has_attr("href") else ""

    def _extract_destination_urls(self, section: BeautifulSoup) -> list[str]:
        urls: list[str] = []
        for link in section.select('a[href*="l.facebook.com/l.php?u="]'):
            href = str(link.get("href", "")).strip()
            destination_url = self._unwrap_facebook_redirect(href)
            if destination_url and destination_url not in urls:
                urls.append(destination_url)
        return urls

    def _unwrap_facebook_redirect(self, href: str) -> str:
        parsed = urlparse(href)
        query_params = parse_qs(parsed.query)
        target_urls = query_params.get("u", [])
        return target_urls[0].strip() if target_urls else href

    def _extract_card_texts(self, section: BeautifulSoup) -> list[str]:
        texts: list[str] = []
        for link in section.select('a[href*="l.facebook.com/l.php?u="]'):
            link_lines = self._visible_text_lines(link)
            for line in link_lines:
                if line not in texts:
                    texts.append(line)
        return texts

    def _extract_body_text(self, lines: list[str]) -> str:
        excluded_prefixes = (
            "Ідентифікатор бібліотеки:",
            "Початок показу:",
        )
        excluded_values = {
            "Активна",
            "Неактивна",
            "Платформи",
            "Прозорість у ЄС",
            "Реклама",
            "Ця реклама має кілька версій",
        }
        body_lines = [
            line
            for line in lines
            if line not in excluded_values
            and not line.startswith(excluded_prefixes)
            and "facebook.com/" not in line
            and not line.startswith("http")
        ]
        return "\n".join(body_lines[:8]).strip()


@dataclass(slots=True)
class GoogleTrendsReader:
    def run(self, offer_url: str) -> dict[str, str]:
        return {
            "offer_url": offer_url,
            "trend_summary": "TODO: implement Google Trends API lookup.",
            "interest_over_time": "TODO: implement time-series trend retrieval.",
        }
