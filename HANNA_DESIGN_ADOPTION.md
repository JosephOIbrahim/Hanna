# Hanna — UI Design Adoption (Interstitial)

Quick session to commit the morning brief design into the Hanna repo as a Phase-1 reference. No data wiring, no server, no production code. The mockup is the design source of truth that future UI-surface sessions will build against.

This sits between Session 01.5 (rules) and Session 02 (compute_producer_phase scaffold) as an interstitial. It does not block Session 02 — they're parallel workstreams.

---

## What Joe is providing

The morning brief HTML mockup (already saved by Joe to the repo before this session starts).

**Expected location:** `Hanna/web/templates/morning_brief.html`

If Joe placed it somewhere else, surface that as a question — do not move it without confirmation.

---

## Step 1 — Switch branch

```bash
git checkout main
git checkout -b ui-design-adoption
```

If `main` doesn't exist yet, branch off the latest merged session line (likely `session-01.5-rules`) and surface that — the main-promotion question from Session 01.5 may still be open.

---

## Step 2 — Validate the file is in position

Confirm `Hanna/web/templates/morning_brief.html` exists and is non-empty. If `Hanna/web/` doesn't exist, create it:

```bash
mkdir -p Hanna/web/templates
mkdir -p Hanna/web/static/css
```

Do not modify the HTML content. The design is locked. If something looks broken, surface it and stop.

---

## Step 3 — Create `Hanna/web/README.md`

This documents the design system so future UI sessions don't have to re-derive it. Create the file with the following content:

```markdown
# Hanna Web Surface

Producer UI for briefs and capsules. Currently mockup-only; data wiring
deferred to a future session.

## Status

Phase 1 — design reference. The morning brief mockup at
`templates/morning_brief.html` is the design source of truth.

## Typography

- Display + technical: JetBrains Mono (weights 400, 500, 600, 700)
- Body sans: Manrope (weights 400, 500, 600, 700)
- Tabular numerics enabled where alignment matters
- font-feature-settings: "kern" 1, "liga" 1, "calt" 1, "ss01" 1

## Palette — seven functional colors, muted earth-cool

| Token         | Hex        | Semantic                           |
|---------------|------------|------------------------------------|
| `--sage`      | `#6B7E73`  | primary action                     |
| `--blue`      | `#6E8893`  | temporal · forcing function        |
| `--honey`     | `#9A8854`  | info · attention                   |
| `--clay`      | `#A0735D`  | escalation (never red)             |
| `--lichen`    | `#7A8556`  | complete · observed                |
| `--lavender`  | `#7E7D8E`  | linked · referenced                |
| `--stone`     | `#8B968F`  | muted · parked                     |

Each has a matching `--tint-*` background variant for callouts and pills.

## Surfaces

- `--bg`: `#ECEFE9` (pale eucalyptus)
- `--bg-elev`: `#DFE5DD` (sage mist)
- `--bg-inset`: `#D2DACE` (deeper sage)
- `--ink`: `#2D3B3D` (deep slate-petrol — never pure black)

## Layout

- Asymmetric gutter system (120px desktop / 52px mobile) holds section
  numbers, portfolio numbers, forcing-function units, property keys.
- Editorial single column, 920px max measure.
- Negative space is treated as deliberately as hierarchy. Every margin
  is a decision, not a default.

## Notion-style structural elements

- **Properties row** — page metadata as key:value pairs, top of brief
- **Callout blocks** — pinned context with icon + tint background
- **Pill component** — universal, seven color variants + `.small` modifier
- **Mention chips** — `@Harlo` `@Octavius` etc. as graph edges
- **Backlinks block** — "Mentioned in" sessions before climax sections

## Roadmap

1. **Phase 1 (current):** Static mockup committed as design reference.
   No data, no server.
2. **Phase 2:** Parameterize templates against producer MCP tool output.
   Template engine decision (Jinja2 vs raw) deferred.
3. **Phase 3:** Lightweight HTTP surface serving locally. Server
   decision (Flask vs FastAPI vs stdlib) deferred. Auth scoped to
   trusted-localhost initially.

## Constraints

- Family-first lockout inherited: UI does not render during lockout.
  Returns lockout state page.
- Cross-substrate read-only inherited: UI reads Harlo state, never writes.
- Patent topics never appear in copy or commentary.
- Design aesthetic: Pentagram-inspired typography, muted earth-cool
  palette, Notion-style structural functionality.
```

---

## Step 4 — Update `BLUEPRINT.md`

Find §5 Specializations. Add a new subsection at the end of that section (after the existing five additions), with this content:

```markdown
### Producer UI Surface

Web-rendered briefs and capsules. Static HTML mockup at
`Hanna/web/templates/morning_brief.html` is the design source of truth.

**Phase 1 (current):** Static mockup committed as design reference.
**Phase 2:** Templates parameterized against producer MCP tool output.
**Phase 3:** Lightweight HTTP surface serving the UI locally.

Design system documented in `Hanna/web/README.md` — Pentagram-inspired
mono-forward typography (JetBrains Mono + Manrope), muted earth-cool
palette with seven functional colors, asymmetric gutter layout,
Notion-style structural elements (properties, callouts, mention pills,
backlinks).

Family-first lockout, cross-substrate read-only, and the rule against
raising patent topics all inherit to this surface.
```

Do not modify any other section of BLUEPRINT.md.

---

## Step 5 — Commit and stop

Three commits on `ui-design-adoption`:

1. `feat(web): add morning brief mockup as Phase-1 design reference`
2. `docs(web): document design system, palette, and UI roadmap`
3. `docs(blueprint): add Producer UI Surface to §5 specializations`

Use the canonical Claude Code commit trailer (established in Session 01.5).

Stop after commit 3. Report to Joe. Session 02 (compute_producer_phase scaffold) can still start whenever Joe approves.

---

## Stop conditions

Surface and pause if:

- The HTML file isn't at `Hanna/web/templates/morning_brief.html` and Joe hasn't told you where it is
- `BLUEPRINT.md` doesn't have a §5 Specializations section (structure has changed since recon)
- Any commit fails for any reason
- The main-promotion question from Session 01.5 needs answering before this branch makes sense

---

## Constraints

- **No production code.** No Python server, no template parameterization, no MCP wiring.
- **No edits to the HTML.** The design is locked at Phase 1.
- **No edits to Harlo or Octavius.** Hanna-only.
- **No patent topics.** Hard rule.
- **Family-first lockout** — if outside Mon–Fri 9 AM to 5 PM EST, pause.

---

## How to work with Joe

- Surface decisions, do not make them.
- One concept per step.
- If the HTML file location is ambiguous, ask before moving anything.
- Keep the commits focused — one concept per commit, as listed above.

---

## Success criterion

- `Hanna/web/templates/morning_brief.html` exists in the repo
- `Hanna/web/README.md` exists with the documented design system
- `BLUEPRINT.md` §5 has the Producer UI Surface subsection
- Three commits on `ui-design-adoption`, canonical trailer format
- Joe reviews. The design is now the reference for future UI sessions.

End of prompt.
