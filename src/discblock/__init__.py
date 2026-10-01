"""discblock: agent-authored interactive UI blocks for Discord bots.

Agents compose typed blocks (text, buttons, selects, modals); this
package validates them against Discord's caps, renders them with
discord.py, and routes clicks back into an agent session.

Core modules:
    blocks   — the block vocabulary (platform-neutral, no discord import)
    payload  — the custom_id encoding contract
    views    — blocks -> discord.ui components
    routing  — InteractionRouter + the SessionBridge protocol
"""

from .blocks import (
    MAX_BUTTONS,
    MAX_BUTTONS_PER_ROW,
    MAX_SELECT_OPTIONS,
    Button,
    ButtonsBlock,
    ImageBlock,
    ModalBlock,
    ModalField,
    Reply,
    SelectBlock,
    SelectOption,
    TextBlock,
    lint,
)
from .payload import ClickPayload, decode, encode
from .routing import AgentTurn, InteractionRouter, SessionBridge
from .views import ModalRegistry, build_modal, build_view

__all__ = [
    "MAX_BUTTONS",
    "MAX_BUTTONS_PER_ROW",
    "MAX_SELECT_OPTIONS",
    "AgentTurn",
    "Button",
    "ButtonsBlock",
    "ClickPayload",
    "ImageBlock",
    "InteractionRouter",
    "ModalBlock",
    "ModalField",
    "ModalRegistry",
    "Reply",
    "SelectBlock",
    "SelectOption",
    "SessionBridge",
    "TextBlock",
    "build_modal",
    "build_view",
    "decode",
    "encode",
    "lint",
]
