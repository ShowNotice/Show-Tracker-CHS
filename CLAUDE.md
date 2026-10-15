# Working in this repo

Rules for Claude Code sessions here, whether interactive or scheduled. The weekly data
routine's own rules are in `pipeline/INSTRUCTIONS.md`; read that before touching
`shows.json` for it. What each file does is in `README.md` and `docs/ARCHITECTURE.md`.

## Owner decisions go into the repo the same day

When the owner decides something in a conversation (a show is in or out, a venue rule,
a source to use or drop), write it where the routine and later sessions will read it,
in the same session:

- a show that must not come back → `pipeline/do_not_add.json`, with `reason: "Owner YYYY-MM-DD: …"`
- a show the owner entered or vouched for → its `confirmed` date in `shows.json`
- a rule → `pipeline/INSTRUCTIONS.md`, dated (`(owner, YYYY-MM-DD)`)
- an open question → `docs/OPEN_ITEMS.md`, or a `flag` + `flagged` date on the show

A decision that lives only in chat or in notes is lost to the routine. This happened
once: the hybrid-events carve-out was in the notes but never in the routine's rules.

## How changes land

- Work on a `claude/` branch made fresh from `origin/main`, open a PR, and squash-merge
  only after its checks pass ("Validate shows.json" for data, "Check worker.js" for
  the Worker).
- Before committing a `shows.json` change, run the commands at the end of `README.md`:
  format, prune, ids, validate against main, and the unit tests.
- Never merge a PR the weekly routine opened unless the owner says so in the
  conversation. Add the `owner-approved` label only when the owner directs it.
- Never change a show's `id`. Unknown values are left out, never "TBA", "—" or "".
- New sources: never scrape Facebook or Instagram. Respect robots.txt. A CAPTCHA or
  bot challenge means stop; don't work around it. A source's first real pull doesn't
  auto-merge.
- Merging `worker.js` or `wrangler.toml` to `main` deploys the Worker
  (`.github/workflows/deploy-worker.yml`).

## Talking to the owner

State whether a claim is established fact, best practice or inference. Flag
uncertainty up front, and check new answers against earlier ones in the conversation.
