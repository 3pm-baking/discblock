"""Render replies into discord.py components.

The only module that imports discord.py. Builds Views and Modals at
runtime from validated blocks — agents never touch discord.ui objects.
"""

from __future__ import annotations

import discord

from . import payload
from .blocks import (
    MAX_BUTTONS_PER_ROW,
    ButtonsBlock,
    ButtonStyleName,
    ModalBlock,
    Reply,
    SelectBlock,
)

_STYLE_MAP: dict[ButtonStyleName, discord.ButtonStyle] = {
    "primary": discord.ButtonStyle.primary,
    "secondary": discord.ButtonStyle.secondary,
    "success": discord.ButtonStyle.success,
    "danger": discord.ButtonStyle.danger,
}


class ModalRegistry:
    """Maps custom_id -> ModalBlock across render and click time.

    Discord's 100-char custom_id cap means modal specs cannot ride in
    the payload; the renderer registers them here and the router looks
    them up when the button is clicked. In-memory by design — a restart
    turns stale modal buttons into a clean "expired" response.
    """

    def __init__(self) -> None:
        self._modals: dict[str, ModalBlock] = {}

    def register(self, custom_id: str, modal: ModalBlock) -> None:
        """Store a modal under a custom_id for click-time lookup."""
        self._modals[custom_id] = modal

    def get(self, custom_id: str) -> ModalBlock | None:
        """Return the modal registered for this custom_id, if any."""
        return self._modals.get(custom_id)


def build_view(
    reply: Reply, modals: ModalRegistry | None = None
) -> discord.ui.View | None:
    """Build a discord.ui.View from a Reply's interactive blocks.

    Returns None when the reply has no interactive blocks — plain
    text/image replies need no view.
    """
    view = discord.ui.View(timeout=None)
    for block in reply.blocks:
        if isinstance(block, ButtonsBlock):
            for row_start in range(0, len(block.buttons), MAX_BUTTONS_PER_ROW):
                row = block.buttons[row_start : row_start + MAX_BUTTONS_PER_ROW]
                for button in row:
                    custom_id = payload.encode(button.value)
                    if button.modal is not None:
                        if modals is None:
                            raise ValueError(
                                "reply has a modal button but no "
                                "ModalRegistry was provided"
                            )
                        modals.register(custom_id, button.modal)
                    view.add_item(
                        discord.ui.Button(
                            label=button.label,
                            style=_STYLE_MAP[button.style],
                            custom_id=custom_id,
                        )
                    )
        elif isinstance(block, SelectBlock):
            view.add_item(
                discord.ui.Select(
                    placeholder=block.placeholder,
                    options=[
                        discord.SelectOption(
                            label=opt.label,
                            value=opt.value,
                            emoji=opt.emoji,
                            default=opt.default,
                        )
                        for opt in block.options
                    ],
                    custom_id=payload.encode(
                        block.options[0].value,
                        {"select": [o.value for o in block.options]},
                    ),
                )
            )
    return view if len(view.children) else None


def build_modal(block: ModalBlock, custom_id: str) -> discord.ui.Modal:
    """Build a discord.ui.Modal from a ModalBlock.

    Field custom_ids are the field labels; submissions come back as
    ``{label: value}`` in the AgentTurn.
    """

    class DynamicModal(discord.ui.Modal):
        def __init__(self) -> None:
            super().__init__(title=block.title, custom_id=custom_id)
            for field in block.fields:
                self.add_item(
                    discord.ui.TextInput(
                        label=field.label,
                        placeholder=field.placeholder,
                        required=field.required,
                        style=(
                            discord.TextStyle.paragraph
                            if field.multiline
                            else discord.TextStyle.short
                        ),
                        custom_id=field.label,
                    )
                )

    return DynamicModal()
