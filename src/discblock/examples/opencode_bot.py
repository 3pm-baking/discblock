"""Minimal opencode + discord.py + discblock example.

One file: a Discord bot that pairs threads with opencode sessions and
lets the agent author interactive UI.

Setup
-----
    opencode serve                          # local server on :4096
    export DISCORD_BOT_TOKEN=...            # Discord bot token
    uv run --extra opencode discblock-example
    # or, without cloning: uvx --from
    #   "discblock[opencode] @ git+https://github.com/3pm-baking/discblock"
    #   discblock-example

@mention the bot in a channel -> it opens a thread, pairs it with an
opencode session, and relays the conversation. To author UI, the agent
ends its reply with a fenced ```discblock JSON payload (see
opencode-agent-instructions.md); the bridge parses it into a Reply and
renders buttons/selects. Clicks and modal submissions flow back into
the session as structured turns.
"""

from __future__ import annotations

import json
import os
import re

import discord
from opencode_ai import AsyncOpencode

from discblock import (
    AgentTurn,
    InteractionRouter,
    Reply,
    TextBlock,
    build_view,
)

DISCBLOCK_FENCE = re.compile(r"```discblock\s*(.*?)\s*```", re.DOTALL)

OPENCODE_BASE_URL = os.getenv("OPENCODE_BASE_URL", "http://127.0.0.1:4096")
OPENCODE_PROVIDER_ID = os.getenv("OPENCODE_PROVIDER_ID", "opencode")
OPENCODE_MODEL_ID = os.getenv("OPENCODE_MODEL_ID", "big-pickle")


def parse_reply(text: str) -> Reply | str:
    """Extract a ```discblock fenced JSON payload from agent text."""
    match = DISCBLOCK_FENCE.search(text)
    if match is None:
        return text.strip()
    prose = (text[: match.start()] + text[match.end() :]).strip()
    blocks = json.loads(match.group(1))["blocks"]
    if prose:
        blocks = [{"type": "text", "content": prose}, *blocks]
    return Reply(blocks=blocks)


def turn_prompt(turn: AgentTurn) -> str:
    """Format a component interaction as the agent's next input."""
    if turn.kind == "modal":
        fields = "\n".join(f"  - {k}: {v}" for k, v in turn.fields.items())
        return f"<user submitted the form '{turn.value}'>\n{fields}"
    return f"<user clicked '{turn.value}'>"


class OpenCodeBridge:
    """SessionBridge over a local opencode server.

    Sessions pair 1:1 with Discord threads, in memory (an example bot
    loses pairing on restart; a real deployment persists the mapping).
    """

    def __init__(self) -> None:
        self.client = AsyncOpencode(base_url=OPENCODE_BASE_URL)
        self.sessions: dict[int, str] = {}  # thread id -> session id

    async def new_session(self, thread_id: int) -> str:
        session = await self.client.session.create(extra_body={})
        self.sessions[thread_id] = session.id
        return session.id

    async def chat(self, thread_id: int, text: str) -> Reply | str:
        """Run one conversational turn (first message or follow-up)."""
        session_id = self.sessions.get(thread_id) or await self.new_session(thread_id)
        return await self._send(session_id, text)

    async def resume(self, session_id: str, turn: AgentTurn) -> Reply | str:
        """Deliver the click's turn to the agent session."""
        return await self._send(session_id, turn_prompt(turn))

    async def _send(self, session_id: str, text: str) -> Reply | str:
        message = await self.client.session.chat(
            session_id,
            provider_id=OPENCODE_PROVIDER_ID,
            model_id=OPENCODE_MODEL_ID,
            parts=[{"type": "text", "text": text}],
            timeout=None,
        )
        return parse_reply(_message_text(message))


def _message_text(message: object) -> str:
    parts = getattr(message, "parts", None) or []
    return "\n".join(
        part.text
        for part in parts
        if getattr(part, "type", None) == "text" and getattr(part, "text", None)
    )


class ExampleBot(discord.Client):
    """Relay Discord threads <-> opencode sessions, with discblock UI."""

    def __init__(self, bridge: OpenCodeBridge) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.bridge = bridge
        self.router = InteractionRouter(bridge, self.session_for)

    async def session_for(self, interaction: discord.Interaction) -> str | None:
        return self.bridge.sessions.get(interaction.channel_id)

    async def on_interaction(self, interaction: discord.Interaction) -> None:
        """Route our components; everything else is not ours."""
        custom_id = (interaction.data or {}).get("custom_id", "") or ""
        if custom_id.startswith("db1|"):
            await self.router.handle(interaction)

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        channel = message.channel
        if isinstance(channel, discord.Thread):
            if channel.id in self.bridge.sessions:
                await self._run_turn(channel, message.content)
            return
        if self.user in message.mentions:
            thread = await message.create_thread(
                name=f"Chat with {message.author.display_name}"
            )
            await self.bridge.new_session(thread.id)
            content = message.content.replace(f"<@{self.user.id}>", "").strip()
            await self._run_turn(thread, content or "Hello!")

    async def _run_turn(self, thread: discord.Thread, text: str) -> None:
        thread_id = thread.id
        if thread_id not in self.bridge.sessions:
            await self.bridge.new_session(thread_id)
            text = text or "Hello!"
        async with thread.typing():
            reply = await self.bridge.chat(thread_id, text)
        await _post(thread, reply, self.router)


async def _post(
    channel: discord.abc.Messageable, reply: Reply | str, router: InteractionRouter
) -> None:
    if not isinstance(reply, Reply):
        reply = Reply(blocks=[TextBlock(content=reply)])
    kwargs: dict = {"content": (reply.text or None)}
    view = build_view(reply, router.modals)
    if view is not None:
        kwargs["view"] = view
    await channel.send(**kwargs)


def main() -> None:
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise SystemExit("Set DISCORD_BOT_TOKEN")
    bot = ExampleBot(OpenCodeBridge())
    bot.run(token)


if __name__ == "__main__":
    main()
