# discblock

Agent-authored interactive UI blocks for Discord bots.

Agents compose typed blocks — text, images, buttons, selects, modals —
as data. discblock validates them against Discord's caps, renders them
with discord.py, and routes clicks back into your agent's session as
structured turns. The agent never touches discord.ui objects, and the
package never owns session state.

```
agent → Reply(blocks=[Text("Which market?"), Buttons([West Asheville], [Black Mtn])])
      → build_view() renders the buttons
user clicks → InteractionRouter decodes the custom_id payload
            → SessionBridge.resume(session_id, AgentTurn(...))
            → the agent continues with the click as its next input
```

## Install

```bash
uv add git+https://github.com/3pm-baking/discblock
```

## Modules

| Module | Purpose |
|---|---|
| `blocks` | The block vocabulary (Pydantic, platform-neutral — no discord import) |
| `payload` | custom_id encode/decode — the contract between views and the router |
| `views` | Blocks → `discord.ui` components |
| `routing` | `InteractionRouter` + the `SessionBridge` protocol (the agent seam) |

## Terminology

Discord calls its system **Message Components** (layout / content /
interactive) plus **Modals**. "Block" is this package's term for the
*agent's* vocabulary — one entry in a Reply's structured payload — kept
distinct from discord.py's `Component` base class on purpose. Mapping:

| discblock | Discord docs |
|---|---|
| `TextBlock` | message `content` (markdown) / Text Display (V2) |
| `ImageBlock` | media / thumbnail (content component) |
| `ButtonsBlock` | an Action Row of Buttons |
| `SelectBlock` | Select Menu |
| `ModalBlock` | Modal with Text Inputs |
| `Reply` | (no Discord equivalent — this package's unit) |

## Example: opencode + discord.py

`examples/opencode_bot.py` is a single-file bot that pairs Discord
threads with opencode sessions (default model: the free
`opencode/big-pickle`) and lets the agent author interactive UI by
ending replies with a fenced `discblock` JSON payload:

```bash
opencode serve                              # local server on :4096
export DISCORD_BOT_TOKEN=...
uv run python examples/opencode_bot.py
```

@mention the bot in a channel; ask it something that has enumerable
choices ("which of our markets should I compare?") and it replies with
buttons. Clicks flow back into the session as structured turns.
Agent-side instructions: `examples/opencode-agent-instructions.md`.

## The seam

Adapt any agent runtime by implementing one method:

```python
class SessionBridge(Protocol):
    async def resume(self, session_id: str, turn: AgentTurn) -> Reply | str: ...
```

Session identity (thread → session mapping) is the consumer's job —
pass a resolver to `InteractionRouter`.

## License

MIT
