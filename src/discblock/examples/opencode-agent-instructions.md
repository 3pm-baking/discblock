# Agent instructions: authoring UI with discblock

The machine-readable core of this guide ships as
`discblock.INSTRUCTIONS` — hosts inject that (header, system prompt,
or instructions file) instead of copying this file. The text below is
the full guide hosts give their agent when they can load it wholesale.

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

## When to reach for controls

Good triggers — the reply is offering the user a genuine fork:

- **Enumerated comparison or plan choice.** "West Asheville or Black
  Mountain?" — two-plus concrete options where the next turn depends
  entirely on the pick.
- **Disambiguation.** The request names something fuzzy ("the lemon
  thing", "that tart we did in May") and the candidate set is known and
  small. Offer the matches instead of guessing.
- **Confirming an expensive or hard-to-reverse action.** Repricing a
  menu, sending an invoice, deleting rows — one confirm/cancel row.
- **Narrowing a multi-step flow.** Market → product → quantity: one
  question per step, each click shrinking the space.
- **An offer of alternatives when blocked.** "No prices for this store
  yet — pick another store / add prices manually."

## When NOT to

- **Informational answers.** A cost table, P&L, or explainer needs zero
  controls — data speaks in markdown tables.
- **One obvious next action.** If there's only one sensible move, do it
  and report; a lone "OK" button is decoration.
- **The user already said what they want.** "Bake 3 cheese cakes" is an
  instruction, not a menu.
- **Re-offering the same buttons after a click.** Never re-post a row
  the user just answered; resume the flow or move on.
- **Speculative forks.** Don't pre-offer branches the user hasn't asked
  about ("want a shopping list too?") — let them type the follow-up.
- **When the choice is open-ended.** Free-text answers want a normal
  reply, or a modal attached to one "Other…" button — never 25 buttons
  guessing at phrasings.

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
