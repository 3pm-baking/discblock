"""Agent-facing instructions for authoring discblock UI.

This is the canonical prompt text hosts inject into their agent's
context — per-message header, system prompt, or instructions file.
One source of truth here; host integrations stay in sync by importing
rather than hand-rolling their own copy.

INSTRUCTIONS is the compact core, sized to live in a per-message
header (~700 chars). The full guide with worked examples, vocabulary
table, and taste rules lives in examples/opencode-agent-instructions.md
and is read on demand.
"""

INSTRUCTIONS = """\
INTERACTIVE_UI: When the next step depends on the user's choice, end
the reply with a fenced ```discblock JSON block — proactively, never
make the user ask for buttons. Vocabulary: {"blocks": [...]} with
{"type": "buttons", "buttons": [{"label": "...", "value": "..."}]};
<=5 choices -> buttons, more -> {"type": "select", "options": [...],
"placeholder": "..."}; free text -> a button with {"modal": {"title":
"...", "fields": [{"label": "..."}]}}. The choice returns as
<user clicked 'value'>. Rules: most replies need no UI; never button
an informational reply; one question per message; never re-offer a row
the user just answered; keep values short and stable.
"""
