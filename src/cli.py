from __future__ import annotations

import argparse
import json

from startup import startup


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="analyze",
        description="Analyze a CPA offer with a LangGraph multi-agent workflow.",
    )
    parser.add_argument(
        "--offer-url",
        required=True,
        help="Offer URL to analyze.",
    )
    parser.add_argument(
        "--traffic-source",
        required=True,
        help="Traffic source for the offer.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    app = startup()
    result = app.invoke(
        {
            "offer_url": args.offer_url,
            "traffic_source": args.traffic_source,
        }
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
