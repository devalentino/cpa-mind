from __future__ import annotations

from typing import Any

from langchain_core.tools import BaseTool, tool

from tools.cpa import OfferReader
from tools.readers import (
    FacebookAdsLibraryReader,
    GoogleTrendsReader,
    LandingReader,
)


def build_offer_reader_tool(offer_reader: OfferReader) -> BaseTool:
    @tool("OfferReader")
    def offer_reader_tool(offer_url: str) -> str:
        """Read the offer page and return cleaned Markdown for further analysis."""
        return offer_reader.run(offer_url)

    return offer_reader_tool


def build_landing_reader_tool() -> BaseTool:
    @tool("LandingReader")
    def landing_reader_tool(landing_urls: list[str]) -> dict[str, Any]:
        """Read and summarize landing page information for landing URLs extracted from the offer."""
        return LandingReader().run(landing_urls)

    return landing_reader_tool


def build_facebook_ads_library_reader_tool() -> BaseTool:
    @tool("FacebookAdsLibraryReader")
    def facebook_ads_library_reader_tool(search_term: str, country: str) -> dict[str, Any]:
        """Read active competitor and creative pattern information from Facebook Ads Library for a localized market search term and target country code."""
        return FacebookAdsLibraryReader().run(search_term, country)

    return facebook_ads_library_reader_tool


def build_google_trends_reader_tool() -> BaseTool:
    @tool("GoogleTrendsReader")
    def google_trends_reader_tool(offer_url: str) -> dict[str, Any]:
        """Read trend information for the offer."""
        return GoogleTrendsReader().run(offer_url)

    return google_trends_reader_tool
