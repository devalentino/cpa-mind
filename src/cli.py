from __future__ import annotations

import argparse
import json
from typing import Any

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
    parser.add_argument(
        "--trace",
        action="store_true",
        help="Stream graph execution updates while the workflow is running.",
    )
    return parser


def _trace_event(event: dict[str, Any]) -> None:
    print("\n[trace]")
    print(json.dumps(event, indent=2, default=str))


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    app = startup()
    initial_state = {
        "offer_url": args.offer_url,
        "traffic_source": args.traffic_source,
    }

    if args.trace:
        result: dict[str, Any] = dict(initial_state)
        for event in app.stream(initial_state, stream_mode="updates"):
            _trace_event(event)
            if isinstance(event, dict):
                for _, update in event.items():
                    if isinstance(update, dict):
                        result.update(update)
        print("\n[final]")
        print(json.dumps(result, indent=2, default=str))
        return

    result = app.invoke(initial_state)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
