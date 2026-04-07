from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="analyze",
        description="Analyze a CPA offer.",
    )
    parser.add_argument(
        "--offer-url",
        required=True,
        help="Offer URL to analyze.",
    )
    parser.add_argument(
        "--trafic-source",
        required=True,
        help="Traffic source for the offer.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    print(f"offer-url: {args.offer_url}")
    print(f"trafic-source: {args.trafic_source}")


if __name__ == "__main__":
    main()
