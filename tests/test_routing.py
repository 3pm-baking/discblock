import discord

from discblock import (
    AgentTurn,
    Button,
    ButtonsBlock,
    InteractionRouter,
    Reply,
    TextBlock,
    deliverable,
    encode,
)


class EchoBridge:
    """Minimal SessionBridge: echoes the turn back as text."""

    def __init__(self, reply: Reply | str | None = None):
        self.turns: list[tuple[str, AgentTurn]] = []
        self.reply = reply if reply is not None else "got it"

    async def resume(self, session_id: str, turn: AgentTurn) -> Reply | str:
        self.turns.append((session_id, turn))
        return self.reply


class FakeInteraction:
    """Duck-typed interaction: enough surface for router.handle()."""

    def __init__(self, custom_id: str, channel_id: int = 42):
        self.type = discord.InteractionType.component
        self.data = {"custom_id": custom_id}
        self.channel_id = channel_id
        self.responses: list = []
        self.response = _ResponseRecorder(self.responses)


class _ResponseRecorder:
    def __init__(self, log: list):
        self._log = log

    async def defer(self):
        self._log.append("defer")

    async def send_message(self, content=None, ephemeral=False):
        self._log.append(("send_message", content, ephemeral))

    async def send_modal(self, modal):
        self._log.append(("send_modal", modal))


class FakeFollowup:
    async def send(self, **kwargs):
        return kwargs


def make_router(reply, sessions: dict | None = None) -> tuple:
    bridge = EchoBridge(reply)
    mapping = sessions or {}

    async def resolver(interaction):
        return mapping.get(interaction.channel_id)

    router = InteractionRouter(bridge, resolver)
    router._followup = FakeFollowup()  # type: ignore[attr-defined]
    return bridge, router


async def test_empty_reply_is_not_delivered():
    bridge, router = make_router(
        Reply(blocks=[TextBlock(content="")]), sessions={42: "sess-0"}
    )
    interaction = FakeInteraction(encode("x"))
    interaction.channel_id = 42
    router._followup = FakeFollowup()

    sent = []
    router._deliver_calls = sent  # type: ignore[attr-defined]

    # patch _deliver to observe whether it is invoked
    original = router._deliver
    observed: list = []

    async def spy(interaction, reply):
        observed.append(reply)
        await original(interaction, reply)

    router._deliver = spy  # type: ignore[method-assign]
    await router.handle(interaction)

    assert bridge.turns[0][1].value == "x"
    assert observed == []  # empty reply skipped


async def test_click_reaches_bridge_and_delivers_text():
    bridge, router = make_router("hello!")
    interaction = FakeInteraction(encode("west_asheville"))
    interaction.channel_id = 42

    posted: list = []

    async def fake_followup_send(**kwargs):
        posted.append(kwargs)

    interaction.followup = type("F", (), {"send": staticmethod(lambda **k: None)})()
    # simpler: router._deliver uses interaction.followup.send
    interaction.followup = _FakeFollowup(posted)

    sessions = {42: "sess-1"}

    async def resolver(i):
        return sessions.get(i.channel_id)

    router = InteractionRouter(bridge, resolver)
    router._followup = None  # type: ignore[attr-defined]

    await router.handle(interaction)

    assert bridge.turns[0] == (
        "sess-1",
        AgentTurn(kind="click", value="west_asheville"),
    )
    assert posted and posted[0]["content"] == "hello!"


async def test_unknown_session_gets_ephemeral_error():
    bridge = EchoBridge("hi")

    async def resolver(i):
        return None

    router = InteractionRouter(bridge, resolver)
    interaction = FakeInteraction(encode("y"))
    await router.handle(interaction)
    assert bridge.turns == []
    assert interaction.responses[-1] == (
        "send_message",
        "No agent session for this thread.",
        True,
    )


class _FakeFollowup:
    def __init__(self, posted: list):
        self.posted = posted

    async def send(self, **kwargs):
        self.posted.append(kwargs)


def test_deliverable_flags():
    text_only = Reply(blocks=[TextBlock(content="hi")])
    assert deliverable(text_only) is True
    assert deliverable(Reply(blocks=[TextBlock(content="")])) is False
    with_controls = Reply(
        blocks=[
            TextBlock(content=""),
            ButtonsBlock(buttons=[Button(label="A", value="a")]),
        ]
    )
    assert deliverable(with_controls) is True
