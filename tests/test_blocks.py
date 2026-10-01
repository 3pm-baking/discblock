import pytest
from pydantic import ValidationError

from discblock import (
    MAX_BUTTONS,
    MAX_BUTTONS_PER_ROW,
    Button,
    ButtonsBlock,
    ModalBlock,
    ModalField,
    Reply,
    SelectBlock,
    SelectOption,
    TextBlock,
    lint,
)


def make_buttons(n: int) -> list[ButtonsBlock]:
    return [
        ButtonsBlock(
            buttons=[
                Button(label=f"b{i}", value=str(i))
                for i in range(start, min(start + MAX_BUTTONS_PER_ROW, n))
            ]
        )
        for start in range(0, n, MAX_BUTTONS_PER_ROW)
    ]


class TestReply:
    def test_text_only_reply_is_valid(self):
        reply = Reply(blocks=[TextBlock(content="hello")])
        assert reply.text == "hello"

    def test_text_blocks_join_with_blank_lines(self):
        reply = Reply(blocks=[TextBlock(content="a"), TextBlock(content="b")])
        assert reply.text == "a\n\nb"

    def test_empty_blocks_rejected(self):
        with pytest.raises(ValidationError):
            Reply(blocks=[])

    def test_oversized_text_rejected(self):
        with pytest.raises(ValidationError):
            Reply(blocks=[TextBlock(content="x" * 2001)])

    def test_button_cap_enforced(self):
        with pytest.raises(ValidationError, match="button cap"):
            Reply(blocks=[*make_buttons(MAX_BUTTONS + 1)])

    def test_exactly_max_buttons_allowed(self):
        reply = Reply(blocks=[*make_buttons(MAX_BUTTONS)])
        assert reply is not None

    def test_row_wrapping_is_renderers_job(self):
        # one block may hold up to MAX_BUTTONS; the renderer wraps rows
        buttons = [
            Button(label=str(i), value=str(i)) for i in range(MAX_BUTTONS_PER_ROW + 1)
        ]
        assert Reply(blocks=[ButtonsBlock(buttons=buttons)])

    def test_too_many_select_options_rejected(self):
        with pytest.raises(ValidationError):
            SelectBlock(
                options=[SelectOption(label=str(i), value=str(i)) for i in range(26)]
            )

    def test_modal_field_cap_enforced(self):
        with pytest.raises(ValidationError):
            ModalBlock(
                title="t",
                fields=[
                    ModalField(label=str(i)) for i in range(MAX_BUTTONS_PER_ROW + 1)
                ],
            )

    def test_discriminated_union_rejects_unknown_type(self):
        with pytest.raises(ValidationError):
            Reply(blocks=[{"type": "chart", "content": "hi"}])


class TestLint:
    def test_clean_text_reply_has_no_warnings(self):
        reply = Reply(blocks=[TextBlock(content="plain answer")])
        assert lint(reply) == []

    def test_orphan_buttons_warn(self):
        reply = Reply(blocks=[ButtonsBlock(buttons=[Button(label="Yes", value="y")])])
        assert any("no text context" in w for w in lint(reply))

    def test_buttons_with_context_are_clean(self):
        reply = Reply(
            blocks=[
                TextBlock(content="Which market?"),
                ButtonsBlock(
                    buttons=[
                        Button(label="West", value="west"),
                        Button(label="Black Mtn", value="bm"),
                    ]
                ),
            ]
        )
        assert lint(reply) == []
