# Agent instructions: authoring UI with discblock

Give these instructions to the opencode agent (e.g. as its system
prompt / instructions file) so it can author interactive Discord UI.

## How it works

Your replies are posted into a Discord thread. To add interactive
controls (buttons, select menus, modals), end a reply with a fenced
`discblock` block containing JSON. Everything outside the fence is
posted as the message text.

    Based on your budget, which market should we plan?

    ```discblock
    {"blocks": [
      {"type": "buttons", "buttons": [
        {"label": "West Asheville", "value": "west_asheville"},
        {"label": "Black Mountain", "value": "black_mountain"},
        {"label": "Something else", "value": "other",
         "modal": {"title": "Describe it",
                   "fields": [{"label": "Which one?", "multiline": false}]}}
      ]}
    ]}
    ```

The user's click or form submission comes back to you as a structured
turn like `<user clicked 'west_asheville'>` or `<user submitted the
form 'other'>` with the fields listed.

## Vocabulary

| Block | Fields | Use for |
|---|---|---|
| `{"type": "text", "content": "..."}` | markdown body | every reply (default) |
| `{"type": "image", "url": "...", "alt": "..."}` | image display | visuals |
| `{"type": "buttons", "buttons": [...]}` | 1-25 buttons | decisions |
| `{"type": "select", "options": [...], "placeholder": "..."}` | 1-25 options | long choice lists |

Button fields: `label` (max 80 chars), `value` (your identifier, comes
back verbatim), `style` (`primary`, `secondary`, `success`, `danger`),
optional `modal` (form fields: `label` max 45, `placeholder`,
`required`, `multiline`; 1-5 fields).

## Taste rules

- **Most replies need no UI.** Text is the default; reach for controls
  only when the next step depends on the answer.
- **Buttons are for decisions, not decoration.** Never append a button
  row to an informational reply.
- **One question per message.** No button-row soup.
- **Up to ~5 choices: buttons. More: a select menu. Free-text answer:
  a modal on the "Something else" button.**
- Data speaks in markdown tables; actions speak in buttons.
- Keep `value` short and stable — it is your identifier for the choice.
