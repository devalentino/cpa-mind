from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from langchain_core.tools import BaseTool, tool


@dataclass(slots=True)
class OfferData:
    offer_url: str
    platform: str
    status: str
    title: str
    description: str
    landing_pages: list[str]
    limitations: list[str]
    audience: str
    notes: list[str]


@dataclass(slots=True)
class OfferParsingContext:
    offer_url: str


class OfferParserStrategy(ABC):
    platform_name: str

    @abstractmethod
    def supports(self, offer_url: str) -> bool:
        pass

    @abstractmethod
    def parse_offer(self, context: OfferParsingContext) -> OfferData:
        pass


class UnsupportedOfferParserStrategy(OfferParserStrategy):
    platform_name = "unsupported"

    def supports(self, offer_url: str) -> bool:
        return True

    def parse_offer(self, context: OfferParsingContext) -> OfferData:
        return OfferData(
            offer_url=context.offer_url,
            platform=self.platform_name,
            status="unknown",
            title="TODO: unsupported platform",
            description="TODO: implement offer parser for this CPA platform.",
            landing_pages=[],
            limitations=["TODO: unknown platform limitations."],
            audience="TODO: unknown audience until platform-specific parser is added.",
            notes=[
                "No platform-specific OfferReader strategy matched this URL.",
                "Add a parser strategy for this CPA dashboard.",
            ],
        )


class TerraleadsOfferParserStrategy(OfferParserStrategy):
    platform_name = "terraleads"

    def __init__(self, login: str, password: str) -> None:
        self._login = login
        self._password = password

    def supports(self, offer_url: str) -> bool:
        hostname = urlparse(offer_url).netloc.lower()
        return "terraleads" in hostname

    def parse_offer(self, context: OfferParsingContext) -> OfferData:
        session_state = self._authenticate()
        offer_snapshot = self._parse_offer_page(context.offer_url, session_state)
        return OfferData(
            offer_url=context.offer_url,
            platform=self.platform_name,
            status=offer_snapshot["status"],
            title=offer_snapshot["title"],
            description=offer_snapshot["description"],
            landing_pages=offer_snapshot["landing_pages"],
            limitations=offer_snapshot["limitations"],
            audience=offer_snapshot["audience"],
            notes=offer_snapshot["notes"],
        )

    def _authenticate(self) -> dict[str, Any]:
        return {
            "authenticated": False,
            "login": self._login,
            "password_configured": bool(self._password),
            "note": "TODO: implement Terraleads dashboard authentication.",
        }

    def _parse_offer_page(
        self,
        offer_url: str,
        session_state: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "status": "unknown",
            "title": "TODO: implement Terraleads offer title parsing.",
            "description": "TODO: implement Terraleads offer description parsing.",
            "landing_pages": ["TODO: implement Terraleads landing page extraction."],
            "limitations": ["TODO: implement Terraleads limitations extraction."],
            "audience": "TODO: implement Terraleads audience extraction.",
            "notes": [
                "Terraleads strategy selected.",
                f"Authentication state: {session_state['note']}",
                f"Offer page parsing is not implemented for {offer_url}.",
            ],
        }


@dataclass(slots=True)
class OfferReader:
    strategies: tuple[OfferParserStrategy, ...]

    def run(self, offer_url: str) -> OfferData:
        context = OfferParsingContext(offer_url=offer_url)
        strategy = self._select_strategy(offer_url)
        return strategy.parse_offer(context)

    def _select_strategy(self, offer_url: str) -> OfferParserStrategy:
        for strategy in self.strategies:
            if strategy.supports(offer_url):
                return strategy
        raise RuntimeError(f"No OfferReader strategy available for URL: {offer_url}")


@dataclass(slots=True)
class LandingReader:
    def run(self, offer_url: str) -> dict[str, Any]:
        return {
            "offer_url": offer_url,
            "landings": [
                {
                    "url": "TODO: implement landing URL collection.",
                    "summary": "TODO: implement landing content analysis.",
                }
            ],
        }


@dataclass(slots=True)
class FacebookAdsLibraryReader:
    def run(self, offer_url: str, traffic_source: str) -> dict[str, Any]:
        return {
            "offer_url": offer_url,
            "traffic_source": traffic_source,
            "competitors": [
                "TODO: implement competitor discovery via Facebook Ads Library."
            ],
            "creative_patterns": [
                "TODO: implement competitor creative pattern analysis."
            ],
        }


@dataclass(slots=True)
class GoogleTrendsReader:
    def run(self, offer_url: str) -> dict[str, Any]:
        return {
            "offer_url": offer_url,
            "trend_summary": "TODO: implement Google Trends API lookup.",
            "interest_over_time": "TODO: implement time-series trend retrieval.",
        }


def build_offer_reader_tool(offer_reader: OfferReader) -> BaseTool:
    @tool("OfferReader")
    def offer_reader_tool(offer_url: str) -> OfferData:
        """Read base offer information such as description, landing pages, limitations, and audience."""
        return offer_reader.run(offer_url)

    return offer_reader_tool


def build_landing_reader_tool() -> BaseTool:
    @tool("LandingReader")
    def landing_reader_tool(offer_url: str) -> dict[str, Any]:
        """Read and summarize landing page information for the offer."""
        return LandingReader().run(offer_url)

    return landing_reader_tool


def build_facebook_ads_library_reader_tool() -> BaseTool:
    @tool("FacebookAdsLibraryReader")
    def facebook_ads_library_reader_tool(
        offer_url: str,
        traffic_source: str,
    ) -> dict[str, Any]:
        """Read competitor and creative pattern information from Facebook Ads Library."""
        return FacebookAdsLibraryReader().run(offer_url, traffic_source)

    return facebook_ads_library_reader_tool


def build_google_trends_reader_tool() -> BaseTool:
    @tool("GoogleTrendsReader")
    def google_trends_reader_tool(offer_url: str) -> dict[str, Any]:
        """Read trend information for the offer from Google Trends."""
        return GoogleTrendsReader().run(offer_url)

    return google_trends_reader_tool
