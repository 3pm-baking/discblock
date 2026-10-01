"""The block vocabulary agents compose replies from.

This module must never import discord.py — it is the platform-neutral
contract between an agent and the renderer. Every block is a Pydantic
model so agent-authored payloads are validated before they reach Discord.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator

# Discord hard caps, mirrored from the API docs
MAX_TEXT_CHARS = 2000
MAX_BUTTONS_PER_ROW = 5
MAX_BUTTON_ROWS = 5
MAX_BUTTONS = MAX_BUTTONS_PER_ROW * MAX_BUTTON_ROWS
MAX_BUTTON_LABEL = 80
MAX_SELECT_OPTIONS = 25
MAX_SELECT_LABEL = 100
MAX_PLACEHOLDER = 150
MAX_CUSTOM_ID = 100
MAX_MODAL_TITLE = 45
MAX_MODAL_LABEL = 45
MAX_MODAL_FIELDS = 5

ButtonStyleName = Literal["primary", "secondary", "success", "danger"]


class TextBlock(BaseModel):
    """A markdown-rendered message body. The default, cheapest block."""

    type: Literal["text"] = "text"
    content: Annotated[str, Field(max_length=MAX_TEXT_CHARS)]


class ImageBlock(BaseModel):
    """An image URL to display inline (via embed attachment)."""

    type: Literal["image"] = "image"
    url: str
    alt: str = ""


class ModalField(BaseModel):
    """One free-text input inside a modal."""

    label: Annotated[str, Field(max_length=MAX_MODAL_LABEL)]
    placeholder: Annotated[str, Field(max_length=MAX_PLACEHOLDER)] | None = None
    required: bool = True
    multiline: bool = False


class ModalBlock(BaseModel):
    """A form presented on click. Attached to a Button, never sent alone."""

    title: Annotated[str, Field(max_length=MAX_MODAL_TITLE)]
    fields: Annotated[
        list[ModalField], Field(min_length=1, max_length=MAX_MODAL_FIELDS)
    ]


class Button(BaseModel):
    """One tappable button. Clicks become agent turns; see payload.py."""

    label: Annotated[str, Field(max_length=MAX_BUTTON_LABEL)]
    value: str
    style: ButtonStyleName = "secondary"
    modal: ModalBlock | None = None


class ButtonsBlock(BaseModel):
    """A row of up to MAX_BUTTONS_PER_ROW buttons."""

    type: Literal["buttons"] = "buttons"
    buttons: Annotated[list[Button], Field(min_length=1, max_length=MAX_BUTTONS)]


class SelectOption(BaseModel):
    """One choice inside a select menu."""

    label: Annotated[str, Field(max_length=MAX_SELECT_LABEL)]
    value: str
    emoji: str | None = None
    default: bool = False


class SelectBlock(BaseModel):
    """A dropdown. Use instead of buttons beyond ~5 options."""

    type: Literal["select"] = "select"
    options: Annotated[
        list[SelectOption],
        Field(min_length=1, max_length=MAX_SELECT_OPTIONS),
    ]
    placeholder: Annotated[str, Field(max_length=MAX_PLACEHOLDER)] | None = None


Block = Annotated[
    TextBlock | ImageBlock | ButtonsBlock | SelectBlock,
    Field(discriminator="type"),
]


class Reply(BaseModel):
    """A complete agent-authored reply: the unit the renderer consumes."""

    blocks: Annotated[list[Block], Field(min_length=1)]

    @model_validator(mode="after")
    def _check_caps(self) -> Reply:
        buttons = sum(
            len(b.buttons) for b in self.blocks if isinstance(b, ButtonsBlock)
        )
        if buttons > MAX_BUTTONS:
            raise ValueError(f"{buttons} buttons exceeds the {MAX_BUTTONS} button cap")
        return self

    @property
    def text(self) -> str:
        """All text blocks joined by blank lines (the message content)."""
        return "\n\n".join(b.content for b in self.blocks if isinstance(b, TextBlock))


def lint(reply: Reply) -> list[str]:
    """Cheap taste guards. Returns human-readable warnings.

    Policy belongs in the agent's prompt; this catches only the
    mechanical mistakes an orphan component row betrays.
    """
    warnings: list[str] = []
    interactive = [
        b for b in reply.blocks if isinstance(b, (ButtonsBlock, SelectBlock))
    ]
    if interactive and not reply.text:
        warnings.append("interactive blocks with no text context — add a TextBlock")
    orphan_modals = [
        btn.label
        for b in reply.blocks
        if isinstance(b, ButtonsBlock)
        for btn in b.buttons
        if btn.modal is not None and not reply.text
    ]
    if orphan_modals:
        warnings.append(f"modal button(s) {orphan_modals} lack a text prompt")
    return warnings
