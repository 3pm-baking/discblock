"""Route component interactions back into agent sessions.

The router owns interaction mechanics (ack, decode, modal round-trip,
reply delivery) but never session identity: the consumer supplies a
resolver mapping the interaction's thread to a runtime session id, and
a SessionBridge that resumes the agent. Nothing here knows how either
works.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Literal, Protocol

import discord
from pydantic import BaseModel

from . import payload
from .blocks import Reply
from .views import ModalRegistry, build_modal, build_view

TurnKind = Literal["click", "modal"]


class AgentTurn(BaseModel):
    """A component interaction, structured as the next agent input."""

    kind: TurnKind
    value: str
    fields: dict[str, str] = {}


class SessionBridge(Protocol):
    """The agent-runtime seam. One implementation per runtime."""

    async def resume(self, session_id: str, turn: AgentTurn) -> Reply | str:
        """Resume the agent with `turn`; return its reply."""
        ...


SessionResolver = Callable[[discord.Interaction], Awaitable[str | None]]


class InteractionRouter:
    """Handle component interactions for a bot using a SessionBridge."""

    def __init__(
        self,
        bridge: SessionBridge,
        session_for: SessionResolver,
        modals: ModalRegistry | None = None,
    ):
        self._bridge = bridge
        self._session_for = session_for
        self._modals = modals if modals is not None else ModalRegistry()

    async def handle(self, interaction: discord.Interaction) -> None:
        """Process one component or modal-submit interaction."""
        custom_id = interaction.data["custom_id"]  # type: ignore[index]
        try:
            click = payload.decode(custom_id)
        except ValueError as exc:
            await interaction.response.send_message(
                f"Stale control: {exc}", ephemeral=True
            )
            return

        if interaction.type is discord.InteractionType.modal_submit:
            await self._resume(
                interaction,
                AgentTurn(
                    kind="modal",
                    value=click.value,
                    fields=_modal_fields(interaction),
                ),
            )
        elif self._modals.get(custom_id) is not None:
            await interaction.response.send_modal(
                build_modal(self._modals.get(custom_id), custom_id)
            )
        else:
            await self._resume(interaction, AgentTurn(kind="click", value=click.value))

    async def _resume(self, interaction: discord.Interaction, turn: AgentTurn) -> None:
        session_id = await self._session_for(interaction)
        if session_id is None:
            await interaction.response.send_message(
                "No agent session for this thread.", ephemeral=True
            )
            return
        await interaction.response.defer()
        reply = await self._bridge.resume(session_id, turn)
        await self._deliver(interaction, reply)

    async def _deliver(
        self, interaction: discord.Interaction, reply: Reply | str
    ) -> None:
        """Post the agent's reply (text content + any new controls)."""
        if not isinstance(reply, Reply):
            reply = Reply(blocks=[{"type": "text", "content": reply}])
        kwargs: dict = {"content": reply.text or None}
        view = build_view(reply, self._modals)
        if view is not None:
            kwargs["view"] = view
        await interaction.followup.send(**kwargs)


def _modal_fields(interaction: discord.Interaction) -> dict[str, str]:
    """Extract submitted values from a modal submit interaction."""
    fields: dict[str, str] = {}
    for action_row in interaction.data.get("components", []):  # type: ignore[union-attr]
        for item in action_row.get("components", []):
            fields[item["custom_id"]] = item.get("value", "")
    return fields
