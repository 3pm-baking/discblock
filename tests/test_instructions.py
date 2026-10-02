"""The shipped agent instructions are load-bearing for every host bot."""

from __future__ import annotations

from discblock import INSTRUCTIONS


def test_nonempty_and_header_sized() -> None:
    # Sized for per-message injection; drift past ~900 chars needs a reason
    assert 0 < len(INSTRUCTIONS) <= 900


def test_names_the_fence_and_click_contract() -> None:
    assert "```discblock" in INSTRUCTIONS
    assert "<user clicked 'value'>" in INSTRUCTIONS


def test_carries_the_restraint_rules() -> None:
    assert "proactively" in INSTRUCTIONS  # user never asks for buttons
    assert "no UI" in INSTRUCTIONS  # most replies need none


def test_fence_example_shows_blocks_payload() -> None:
    assert '{"blocks": [' in INSTRUCTIONS
    assert '{"label":' in INSTRUCTIONS and '"value":' in INSTRUCTIONS
