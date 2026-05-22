# Producer lens — what Hanna could find useful

**Date:** 2026-05-22
**Posture anchor:** [Rule 36](../RULES.md) — surface, don't decide. [Rule 34](../RULES.md) — family-first as architectural primitive. [HANNA_BLUEPRINT.md](../HANNA_BLUEPRINT.md) §1 — *"producer-rhythm twin: tracks what's in-flight, what's blocking, and what's approaching across an active portfolio of products."*

This document is first-principles thinking about Hanna's effectiveness as a work-task producer for Joe specifically — a VFX director who lives in Houdini and on iPhone, juggling ~4 portfolio products at different lifecycle stages. The thinking expands beyond the ratified [D006](DECISIONS.md) Calendar output and [D007](DECISIONS.md) per-product `.md` input surfaces into a *medium-scope* exploration of two additional MCP integrations (Gmail, Files/Drive) and a catalogue of producer patterns Hanna could surface that map to Joe's actual work.

Nothing in this doc is ratified. It is exploration — a feeder for future D-entries (likely D009 Gmail, D010 Files), and a brief composer's reference for what "useful" looks like.

---

## §1 What "effective producer" means for Joe

A producer in VFX is not a manager. The producer's job is to track, coordinate, and surface — never to direct. The director directs. Hanna inherits this posture verbatim per Rule 36.

For Joe specifically, *effective* means:

- **Surfaces decisions Joe would otherwise make fatigued or under-informed.** The Q2 review is in 5 working days; the slides aren't started; the vendor is late. Hanna names these in the morning brief as observations. Joe decides what to do.
- **Collapses the cognitive cost of multi-product portfolio juggle.** ~4 products in flight (`harlo`, `octavius`, `moneta`, `comfy_cozy`) at different lifecycle stages. Without Hanna, Joe context-switches between them on every check-in. With Hanna, the morning brief ranks them by what needs attention today.
- **Reduces forcing-function surprises.** A Q-review in 5 working days reads differently than one in 5 weeks. Decay-by-distance is the signal; the brief surfaces it.
- **Never interrupts.** [D006](DECISIONS.md) ratified Calendar (not push notifications, not iMessage) precisely because the producer's voice is calm, not loud. An interruptive producer is a bad producer.
- **Respects family-first as structural, not as setting.** Rule 34. The producer's voice goes silent at 17:00 ET Friday and stays silent until 09:00 ET Monday. No exceptions without explicit `override_token`.
- **Surfaces the why-trail.** Past decisions are queryable. "Why did we go with Calendar over iMessage?" → Hanna points at D006.

Effectiveness is measured not in how much Hanna produces but in how much Joe doesn't have to remember.

---

## §2 Ratified input surfaces — what Hanna reads today

Per [D007](DECISIONS.md), Hanna's input surface for v1 is three-layered. Layer (a) is the MVS; (b) and (c) are deferred follow-ons.

### §2.1 Per-product `.md` files (D007.1–D007.6, ratified, MVS)

`data/products/{name}.md` — one file per portfolio product. Joe edits the file directly when state changes. File mtime is the freshness signal. Initial set: `harlo`, `octavius`, `moneta`, `comfy_cozy`.

File shape per [D007.1–D007.3](DECISIONS.md):

```markdown
---
product: harlo
status: in_flight
last_review_iso: 2026-05-22
---

## Status
[1–3 sentences naming where the product currently is.]

## Blockers
- [Bullet list of blockers; empty means "no blockers."]

## Approaching forcing functions
- [Bullet list with dates; e.g., "2026-05-30: Q2 review presentation"]

## Notes
[Free-form. Anything Joe wants to surface to Hanna that doesn't fit above.]
```

What Hanna reads from this surface:
- **Status enum** (`in_flight` / `parked` / `shipped` / `exploring`) → product gets weighted in the brief; `parked` products surface only on weekly review.
- **Blockers** → if any blocker has aged beyond `last_review_iso - 7 days`, escalate in the brief.
- **Approaching forcing functions** → date-keyed; the `compute_brief_priority` heuristic weights by `(deadline - today) ≤ 5 working days`.
- **Notes** → free-form context the composer can quote selectively.

This is the ratified ground. Implementation lands in L4a per [`ROADMAP.md`](ROADMAP.md).

### §2.2 Calendar reads — layer (b), deferred per D007.4

Per [HANNA_BLUEPRINT.md](../HANNA_BLUEPRINT.md):199, *"Hanna reads Joe's existing calendar(s) over Google Calendar / Apple Calendar APIs and treats dated events tagged with portfolio-product keywords as forcing functions."* This is layer (b) of the input surface, deferred to a follow-on D-entry per [D007.4](DECISIONS.md).

When it lands, it complements §2.1 by catching forcing functions Joe doesn't manually log in the product `.md` files. Cross-reference logic: events with titles or notes matching product-name keywords (case-insensitive) become forcing-function entries in that product's bucket.

### §2.3 Conversational MCP tools — layer (c), deferred per D007.5

`hanna_log`, `hanna_block`, `hanna_unblock` — single-sentence-becomes-state from any Claude session. Joe types `/hanna_log "octavius: shipped the formation grammar today"` and the tool appends to `data/products/octavius.md` under the right section. Deferred until the `mcp_tools` lane (L6) lands per [ROADMAP.md](ROADMAP.md).

These tools enable the "I'm in a thinking session and want to log a state change without leaving" workflow — important for a creative director whose context-switch cost is high.

---

## §3 Additional input surfaces — Gmail + Files (medium-scope, proposed, no D-entry yet)

The medium-scope addition expands the input layer with two MCP integrations Joe likely already uses daily but Hanna doesn't read yet. Each would land as a future MoE dispatch behind a new D-entry.

### §3.1 Gmail forcing-function detection (proposed D009)

**Why.** Many of Joe's forcing functions originate in email — a producer mentions a Q2 review date, a vendor confirms a delivery slot, a director-of-photography schedules a creative review. Today these enter Hanna only if Joe manually transcribes them into the product `.md` files. The transcription cost is real; lots of these slip.

**What Hanna would read.** Gmail MCP exposes `search_threads`, `get_thread`, `list_labels`, `label_thread`. Read-only access fits Rule 35 (Hanna never writes Gmail; never replies on Joe's behalf).

**Detection patterns.** For each product, configure keywords (e.g., `harlo`: ["harlo", "cognitive twin", "v9"]; `octavius`: ["octavius", "formation", "multi-agent"]). Hanna runs a daily search across new threads (since `last_review_iso`) and extracts:
- **Date mentions** — *"on Friday at 3pm"*, *"Q2 review"*, *"by end of month"* — become forcing-function candidates for the matching product.
- **Block mentions** — *"vendor hasn't replied"*, *"waiting on legal"*, *"asset library locked"* — become blocker candidates.
- **Status changes** — *"shipped"*, *"approved"*, *"rolled back"* — become status-update candidates.

Each extraction surfaces in the morning brief as: *"Gmail thread [subject] mentions [date] for [product] — surfaced as forcing function. Confirm or dismiss in `data/products/{product}.md`."* Hanna proposes, Joe ratifies.

**Implementation lane.** Future MoE dispatch — Bridge Engineer + Brief Composer. Module `src/inputs/gmail_reader.py`. Effort: ~1 session post-L4. Depends on Gmail MCP being authenticated against Joe's account.

**Rule compliance.**
- **Rule 35.** Read-only. Hanna calls `search_threads` and `get_thread`. No `create_draft`, no `label_thread`, no write-side surface.
- **Rule 34.** Gmail reads happen on the same wall-clock cadence as the briefs — Mon–Fri 09–17 ET only. Outside hours, no Gmail polling.
- **Rule 36.** Extractions are surfaced as candidates, never auto-applied to product files. *"Hanna proposes; Joe ratifies in the .md file."*

### §3.2 Files/Drive deliverable surface (proposed D010)

**Why.** Joe's deliverables live in files: slides for the Q2 review, scripts for the vendor pitch, Houdini hipnc files for the cognitive-twin demo. Today Hanna has no awareness of these. The producer should know what's *attached* to each forcing function and surface their staleness (a slide deck untouched for 14 days while the review is 5 days out is a signal).

**What Hanna would read.** Files MCP exposes `search_files`, `read_file_content`, `get_file_metadata`, `list_recent_files`. Read-only access fits Rule 35.

**Two integrations.**

1. **Per-product `.md` files become Drive-backed (optional).** If Joe wants cross-device editing (iPad, phone), the `data/products/{name}.md` files can live on Drive instead of (or mirrored to) the local repo. Hanna reads the Drive copy when present. Joe edits from any device.

2. **Attached deliverables surfaced in briefs.** Each product file can optionally name attached deliverables in a new YAML frontmatter field:
   ```yaml
   ---
   product: harlo
   status: in_flight
   last_review_iso: 2026-05-22
   deliverables:
     - drive_id: "1ABC..."
       name: "Q2 Review Deck"
       relevant_to_forcing_function: "2026-05-30 Q2 review"
   ---
   ```
   Hanna calls `get_file_metadata(drive_id)` and compares the file's `modifiedTime` against `last_review_iso`. If the deliverable is stale relative to the forcing function (e.g., deck untouched 14 days while the review is in 5 days), the brief surfaces it.

**Implementation lane.** Future MoE dispatch — Bridge Engineer + Brief Composer. Module `src/inputs/drive_reader.py`. Effort: ~1 session.

**Rule compliance.**
- **Rule 35.** Read-only on Files MCP. No `create_file`, no `copy_file`, no `download_file_content` write-back.
- **Rule 34.** Same wall-clock cadence as the briefs.
- **Rule 36.** Surfaced as observations. *"Q2 deck untouched 14 days; review in 5 days."* Joe decides what to do.

### §3.3 Why these two and not the broader set

The full available MCP set includes Calendar (ratified), Gmail (proposed §3.1), Files (proposed §3.2), Spotify, Trails, GitHub, Hugging Face, Vercel. Joe ratified the *medium* scope — Gmail + Files only — explicitly excluding Spotify/Trails/GitHub from this lens.

The exclusion rationale (captured for future reference):
- **Spotify.** Energy/focus signal (currently-playing as a mood proxy) is interesting but speculative. The Harlo bridge already provides a more direct burnout/state read. Marginal value over Harlo is unclear; speculative inclusion would be feature-not-warranted per the project's "smallest correct change" discipline.
- **Trails.** Off-grid weekend context is interesting for understanding lockout-extension patterns (Joe disappears for a Sunday hike → Monday's brief carries different energy). But this is a *Rule 34* read, not a producer read. Belongs in a future Rule-34-refinement session, not the producer lens.
- **GitHub.** Build/ship state across the portfolio is technically a producer signal but is already partially captured in the product `.md` files (Joe writes "shipped" in the status field). Direct GitHub MCP integration would duplicate that signal without obvious additive value at v1.
- **Hugging Face, Vercel.** Operational substrate (model awareness, deploy ops). Producer-irrelevant.

The medium scope is the smallest correct expansion. Broader scope is a future session.

---

## §4 Producer patterns from VFX-director world

Beyond input surfaces, Hanna can surface patterns Joe's actual job demands. Each is a *what the brief composer should know how to do*, mapped to the data sources above.

### §4.1 Multi-product portfolio juggle

**Pattern.** ~4 products in flight; each at different lifecycle stages. Without ranking, the morning brief becomes a flat list — useless.

**What Hanna does.** `compute_brief_priority` (L4a) ranks by `(deadline_proximity × in_flight_count)`. The morning brief leads with the top 1–2 products and provides a one-line status for the rest. Weekly review broadens to all four.

**Effectiveness signal.** Joe reads the brief and can act on the top product without scanning. Time-to-decision drops.

### §4.2 Forcing-function lead time

**Pattern.** A Q-review in 5 working days needs different surfacing than one in 5 weeks. Hanna's voice is not a bullhorn; it modulates.

**What Hanna does.** Decay-by-distance: forcing functions within 5 working days get a leading-line surface in the morning brief ("Q2 review in 4 days — deck untouched 14 days"). Beyond 5 days, they appear in the weekly Monday 30k review, not daily. Beyond 30 days, monthly review only.

**Effectiveness signal.** Joe is not nagged about a far-future deadline. The closer it gets, the higher Hanna lifts it. Joe's attention budget is preserved.

### §4.3 Energy/state awareness

**Pattern.** The Harlo bridge exposes `read_burnout_level` and `read_state`. Joe's cognitive state is data, not noise.

**What Hanna does.** When state is RED (Rule 18), the morning brief leads with a state observation: *"Your state reads RED. Today's portfolio rank is preserved below for context, but consider deferring the hardest item."* No prescription. Surface + context.

When state is GREEN and burnout is low, the brief leads with the highest-leverage item, full stop.

**Effectiveness signal.** Joe sees state-shaped briefs. The producer is aware that Joe is human, not a queue.

### §4.4 Cross-product synthesis

**Pattern.** When two products share a blocker (same vendor late, same legal review pending), it should surface as one observation, not two.

**What Hanna does.** `compute_brief_priority` includes a cross-product blocker-deduplication pass. The brief composer surfaces shared blockers in their own section: *"Cross-product blocker: legal review for vendor contract X is gating both Octavius and Moneta. Surfaced once."*

**Effectiveness signal.** Joe sees the structural blocker, not its instances. Unblocking it unblocks both products; the brief makes the leverage visible.

### §4.5 Decision archive surfacing

**Pattern.** Joe asks in a future session: *"Why did we pick Calendar over iMessage?"* Without an archive, this is a memory game.

**What Hanna does.** [`docs/DECISIONS.md`](DECISIONS.md) is the queryable why-trail. A future `mcp_tools` surface (L6) exposes `hanna_recall_decision(query: str)` that grep-searches the file for D-entries matching the query and returns the matched reasoning. Joe gets the D006 reasoning instantly.

**Effectiveness signal.** Joe's past decisions are durable context, not lost cognitive load.

### §4.6 Brief-archive trend surfacing

**Pattern.** Daily briefs accumulate in `data/hanna.sqlite` (already implemented at the PoC level per `scripts/first_hanna_brief.py:107–115`). A week of briefs is a corpus.

**What Hanna does (future).** Weekly Friday harvest reads the last 5 briefs and surfaces patterns: *"This week you noticed octavius blockers on Mon, Wed, Fri. Pattern: vendor-quote-aging. Surfaced for the weekly review."*

**Effectiveness signal.** Joe sees his own week reflected back. Producer becomes a mirror, not just a forward-looking surface.

---

## §5 Anti-patterns — what Hanna should NOT do

Each anti-pattern is a rule violation if attempted.

- **Push notifications.** [D006](DECISIONS.md) ratified Calendar (non-interruptive). iMessage, macOS notifications, browser pings are anti-patterns. Calendar event sitting in day-view is the only surface.
- **Prescriptions.** *"You should ship the deck today."* Violates Rule 36. The brief surfaces observations; Joe decides actions.
- **Fire outside Mon–Fri 09–17 ET.** Violates Rule 34. The lockout is structural; no `override_token`-less brief lands outside hours.
- **Writing to Harlo.** Violates Rule 35. Hanna reads `coach` (heavy drive) and the cheap reads per [D001](DECISIONS.md). Never writes.
- **Speaking for Joe.** Replying to Gmail threads on his behalf, drafting docs, sending iMessages. Violates Rule 35 (Gmail/Files surfaces are read-only).
- **Patent topics.** Rule 37. Never raised. Zero exceptions.
- **Synthesizing what wasn't asked.** Joe asks for the morning brief; Hanna does not append "and also, here are 5 things I noticed in your calendar last week." Stay scope-tight; surface relevance only.

---

## §6 Open producer-lens questions (parked for future D-entries)

- **Cross-day persistence.** Does today's brief reference yesterday's open items, or is each brief stateless? Architectural decision.
- **Voice modulation per phase.** Does the morning brief voice differ from the evening capsule voice? From the monthly review voice?
- **Brief length budget.** Morning brief (concise, ≤200 words?) vs. weekly review (broader, ≤500 words?) vs. monthly review (50k feet, ≤1000 words?). Per-phase concision envelope.
- **Override surface UX.** When Joe authorizes outside-hours work via `override_token`, how does the token surface present? Modal in calendar, slash command, signed iMessage? (Cross-cuts D006 channel choice.)
- **State-blind degradation voice.** When the Harlo bridge is unreachable, the brief composer falls back to a state-blind voice. What does state-blind mean for tone? Currently the PoC explicitly says *"Harlo edge unreachable — Hanna is operating state-blind."* Is that the right voice, or should state-blind feel different?
- **Forcing-function entity-extraction model.** Gmail integration (§3.1) needs to extract dates from email prose. Hand-coded regex? LLM call? Hybrid?
- **What about products Joe stops touching?** A product file untouched 30 days — does Hanna surface its dormancy, or stay silent? Producer discipline question.

These are seed questions for future producer-lens sessions, not blocking the immediate buildout.

---

## §7 Cross-references

- [`HANNA_BLUEPRINT.md`](../HANNA_BLUEPRINT.md) §1 — producer-rhythm twin definition.
- [`HANNA_BLUEPRINT.md`](../HANNA_BLUEPRINT.md) §5.6 — three-layer input surface sketch.
- [`HANNA_BLUEPRINT.md`](../HANNA_BLUEPRINT.md) §7 — producer phase machine.
- [`RULES.md`](../RULES.md) §34 — family-first lockout.
- [`RULES.md`](../RULES.md) §35 — cross-substrate writes prohibited.
- [`RULES.md`](../RULES.md) §36 — surface, don't decide.
- [`docs/DECISIONS.md`](DECISIONS.md) D001 — Rule 35 permissive read of `coach`.
- [`docs/DECISIONS.md`](DECISIONS.md) D006 — Calendar channel ratified.
- [`docs/DECISIONS.md`](DECISIONS.md) D007 — per-product `.md` input surface MVS ratified.
- [`docs/ROADMAP.md`](ROADMAP.md) — buildout lane DAG executing against this lens.
- [`docs/UI_UX_MAP.md`](UI_UX_MAP.md) — visual map of the surfaces this lens describes.

---

*The producer's value is not its output volume. It is the cognitive load it removes from Joe's day.*
