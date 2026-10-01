import discord
import pytest

from discblock import (
    Button,
    ButtonsBlock,
    ModalBlock,
    ModalField,
    ModalRegistry,
    Reply,
    SelectBlock,
    SelectOption,
    TextBlock,
    build_modal,
    build_view,
    decode,
    encode,
)


class TestBuildView:
    def test_plain_text_reply_needs_no_view(self):
        reply = Reply(blocks=[TextBlock(content="hello")])
        assert build_view(reply) is None

    def test_buttons_render_with_encoded_custom_ids(self):
        reply = Reply(
            blocks=[
                ButtonsBlock(
                    buttons=[
                        Button(label="Yes", value="print", style="success"),
                        Button(label="No", value="skip"),
                    ]
                )
            ]
        )
        view = build_view(reply)
        assert view is not None
        by_custom_id = {
            c.custom_id: c for c in view.children if isinstance(c, discord.ui.Button)
        }
        assert set(by_custom_id) == {encode("print"), encode("skip")}
        assert by_custom_id[encode("print")].label == "Yes"
        assert by_custom_id[encode("print")].style is (discord.ButtonStyle.success)

    def test_six_buttons_wrap_into_rows(self):
        buttons = [Button(label=str(i), value=str(i)) for i in range(6)]
        reply = Reply(blocks=[ButtonsBlock(buttons=buttons)])
        view = build_view(reply)
        assert view is not None
        assert len(view.children) == 6

    def test_select_renders_options(self):
        reply = Reply(
            blocks=[
                SelectBlock(
                    options=[
                        SelectOption(label="West", value="west"),
                        SelectOption(label="Black Mtn", value="bm"),
                    ],
                    placeholder="Pick one",
                )
            ]
        )
        view = build_view(reply)
        assert view is not None
        select = next(c for c in view.children if isinstance(c, discord.ui.Select))
        assert select.placeholder == "Pick one"
        assert [o.value for o in select.options] == ["west", "bm"]


class TestModals:
    def make_modal_reply(self) -> Reply:
        return Reply(
            blocks=[
                TextBlock(content="Something else?"),
                ButtonsBlock(
                    buttons=[
                        Button(
                            label="Type it",
                            value="other",
                            modal=ModalBlock(
                                title="Describe it",
                                fields=[ModalField(label="What?")],
                            ),
                        ),
                        Button(label="No", value="skip"),
                    ]
                ),
            ]
        )

    def test_modal_button_payload_stays_light(self):
        modals = ModalRegistry()
        view = build_view(self.make_modal_reply(), modals)
        assert view is not None
        button = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button) and c.custom_id == encode("other")
        )
        decoded = decode(button.custom_id)
        assert decoded.value == "other"
        assert decoded.action is None  # modal rides in the registry

    def test_modal_registered_for_click_time(self):
        modals = ModalRegistry()
        build_view(self.make_modal_reply(), modals)
        custom_id = encode("other")
        assert modals.get(custom_id) is not None
        assert modals.get(custom_id).title == "Describe it"

    def test_modal_button_without_registry_raises(self):
        with pytest.raises(ValueError):
            build_view(self.make_modal_reply())

    def test_build_modal_shape(self):
        block = ModalBlock(
            title="Describe it",
            fields=[
                ModalField(label="What?", multiline=True, required=False),
            ],
        )
        modal = build_modal(block, "db1|x")
        assert modal.title == "Describe it"
        assert modal.custom_id == "db1|x"
        inputs = modal.children
        assert inputs[0].label == "What?"
        assert inputs[0].style is discord.TextStyle.paragraph
        assert inputs[0].required is False
