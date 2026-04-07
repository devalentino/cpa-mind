from __future__ import annotations

import pytest

from cli import main


@pytest.mark.integration
def test_analyze_terraleads_offer_for_facebook(capsys) -> None:
    main(
        [
            "--offer-url",
            "https://terraleads.com/acp/offer/view?id=10617",
            "--traffic-source",
            "facebook",
        ]
    )

    captured = capsys.readouterr()
    assert captured.out.strip()
