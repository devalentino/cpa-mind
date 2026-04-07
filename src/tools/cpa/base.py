from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

class OfferParserStrategy(ABC):
    platform_name: str

    @abstractmethod
    def supports(self, offer_url: str) -> bool:
        pass

    @abstractmethod
    def parse_offer(self, offer_url: str) -> str:
        pass


class UnsupportedOfferParserStrategy(OfferParserStrategy):
    platform_name = "unsupported"

    def supports(self, offer_url: str) -> bool:
        return True

    def parse_offer(self, offer_url: str) -> str:
        return (
            f"# Unsupported CPA Platform\n\n"
            f"Offer URL: {offer_url}\n\n"
            "TODO: implement offer parser for this CPA platform.\n\n"
            "- No platform-specific OfferReader strategy matched this URL.\n"
            "- Add a parser strategy for this CPA dashboard."
        )


@dataclass(slots=True)
class OfferReader:
    strategies: tuple[OfferParserStrategy, ...]

    def run(self, offer_url: str) -> str:
        strategy = self._select_strategy(offer_url)
        return strategy.parse_offer(offer_url)

    def _select_strategy(self, offer_url: str) -> OfferParserStrategy:
        for strategy in self.strategies:
            if strategy.supports(offer_url):
                return strategy
        raise RuntimeError(f"No OfferReader strategy available for URL: {offer_url}")
