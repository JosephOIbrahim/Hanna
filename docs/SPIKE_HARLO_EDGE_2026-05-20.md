# Spike — Harlo MCP edge reconciliation

**Date:** 2026-05-20
**Scope:** Audit §12.5 — verify whether Hanna's v0.1.0 bridge contract (`read_state` / `read_prediction` / `read_burnout_level`) is achievable against Harlo's actually-exposed MCP tools.
**Duration:** ~30 minutes (single Code session).
**Verdict:** **Achievable as compositions over `status` and `coach`.** No blueprint change required; bridge method names should be kept (they describe Hanna's intent), bridge *implementations* call Harlo's real surface.

---

## 1. Harlo's actually-exposed read-side tool surface

Read-only tools (safe for Hanna to call per Rule 35):

| Tool | Side effects | Returns |
|---|---|---|
| `status` | Advances `exchange_index` only — no trace authored, no delegate routed, no save | Full `v9` block: `engine`, `routing`, `prediction`, `state`, `dynamics`, `schedule`, `allostasis` |
| `coach` | **Drives full v9 exchange** (author → DAG → route → delegate → observe → predict → save). Authors traces, advances counter, may route through delegates, may refresh `prediction` | `coach_block` (XML system prompt with recent traces), `cognitive_context` (rendered ASCII summary), `v9` |
| `recall` | Advances `exchange_index`; SDR semantic search across Warm tier | `context`, `traces`, `confidence`, `v9` |
| `query_past_experience` | Advances `exchange_index`; federated Hot (FTS5) + Warm (SDR) | `results`, `count`, `v9` |
| `patterns` | Advances `exchange_index`; runs pattern detection across stored traces | `patterns`, `count`, `v9` |

Write-side tools (Hanna **must never call** per Rule 35): `store`, `stage_reload`, `resolve_verifications`, `trigger_cognitive_recalibration`.

---

## 2. The `v9` envelope is universal

Every read-side tool wraps its payload in a `v9` block with at least:

```jsonc
"v9": {
  "exchange_index": <int>,
  "engine": {                       // status + coach only
    "stage_type": "real_usd",
    "predictor": false,             // <-- predictor liveness flag
    "observations_logged": <int>,
    "delegates_registered": <int>,
    "memory_queue_size": <int>,
    "pending_save": false
  },
  "routing": { "delegate_id": "claude", "expert": "exploring" },
  "prediction": null,               // <-- prediction slot (currently null)
  "state": {                        // status + coach only
    "momentum": "COLD_START",
    "burnout": "GREEN",
    "energy": "MEDIUM",
    "altitude": "GROUND"
  },
  "dynamics": {                     // status + coach only
    "burst_phase": "NONE",
    "session_exchange_count": <int>,
    "exchanges_without_break": <int>
  },
  "schedule": {                     // status + coach only
    "kind": "WORK",
    "override_reason": ""
  },
  "allostasis": {                   // status + coach only
    "load": 0.0214,
    "trend": "STABLE"
  }
}
```

Hanna's bridge can rely on this envelope shape across all read-side tools.

---

## 3. Mapping v0.1.0 contract → real surface

| v0.1.0 bridge method | Maps to | Cost | Notes |
|---|---|---|---|
| `read_state()` | `status` → `v9` | Cheap (no exchange driven) | Returns the entire cognitive state block — momentum, burnout, energy, altitude, schedule, allostatic load, dynamics — in one call. **This is the workhorse read.** |
| `read_burnout_level()` | `status` → `v9.state.burnout` | Cheap (projection over `read_state`) | One of `GREEN` / `YELLOW` / `ORANGE` / `RED`. **No separate burnout tool exists** — and none is needed; the field is already in the cheap status call. |
| `read_prediction()` | `status` → `v9.prediction` *(passive read)* or `coach` → `v9.prediction` *(active drive)* | Cheap (passive) / heavy (active) | Two distinct semantics — see §5. |

**Conclusion:** the v0.1.0 method names describe Hanna's *intent* correctly. The implementation calls Harlo's real surface (`status` for almost everything; `coach` only when a fresh exchange is genuinely needed).

---

## 4. Predictor is currently inactive

Both `status` and `coach` returned `v9.engine.predictor: false` and `v9.prediction: null`.

**Implication for §12.4 (predictor cold-start):** Harlo itself does not currently expose a live XGBoost predictor over the MCP surface — there is nothing for Hanna to "bootstrap from." The v0.1.0 default ("bootstrap from Harlo's predictor for the first weeks") is moot until Harlo's predictor flips to `true`.

**Recommendation:** `read_prediction()` returns `None` cleanly when `v9.prediction is None`. Hanna must degrade gracefully — brief composition cannot depend on prediction being present. This aligns with the §9 hard rule that Hanna degrades to state-blind mode when Harlo signal is unavailable.

---

## 5. Cost asymmetry — `status` is cheap, `coach` is heavy

Across the spike's five calls, `exchange_index` advanced 1 → 2 → 3 → 4 → 5. Every read-side call increments the counter. But the *work* per call differs by an order of magnitude:

- **`status`** — assembles the current state snapshot from in-memory engine state. No traces authored, no delegate routed, no save. Suitable to call on every Hanna MCP tool entry for lockout checks and lightweight state reads.
- **`coach`** — drives the full v9 exchange: builds the coach block from recent traces, routes through the delegate registry, may produce a fresh prediction, and saves the exchange. Heavy. Suitable to call **at most once per brief composition**, never on the hot path of a lockout gate.

**Bridge implication:** the bridge needs two distinct verbs.

---

## 6. Proposed revised bridge contract

```python
# src/harlo_bridge.py — read-only client over MCP-stdio.
# Calls only status / coach / recall / query_past_experience / patterns.
# Never calls store, stage_reload, resolve_verifications, trigger_cognitive_recalibration.

class HarloBridge:

    # --- Cheap reads (call freely) -----------------------------------

    def read_state(self) -> dict:
        """Cognitive state snapshot. Maps to Harlo's `status` tool.
        No cognitive exchange driven. Returns the v9 block."""
        return self._call("status")["v9"]

    def read_burnout_level(self) -> str:
        """One of GREEN | YELLOW | ORANGE | RED.
        Projection over read_state — same underlying call."""
        return self.read_state()["state"]["burnout"]

    def read_schedule(self) -> dict:
        """{kind: WORK | FAMILY | OFF_HOURS, override_reason: str}.
        Projection over read_state."""
        return self.read_state()["schedule"]

    def read_prediction(self) -> dict | None:
        """Currently-posted prediction. None if Harlo's predictor is inactive
        (v9.engine.predictor is False). Does NOT drive a fresh exchange.
        For a fresh prediction, use drive_coaching_exchange."""
        return self.read_state()["prediction"]

    # --- Heavy drive (call sparingly) --------------------------------

    def drive_coaching_exchange(self, session_id: str | None = None) -> dict:
        """Drives a full v9 cognitive exchange via Harlo's `coach` tool.
        Heavy — authors traces, routes through delegates, may refresh prediction,
        saves the exchange. Use at most once per brief composition.
        Returns {coach_block, cognitive_context, v9}."""
        return self._call("coach", session_id=session_id)

    # --- Memory queries (read-side, semantic) ------------------------

    def recall(self, query: str, depth: str = "normal") -> dict:
        """Semantic SDR search across Warm tier. depth: 'normal' (top 5) or 'deep' (top 15)."""
        return self._call("recall", query=query, depth=depth)

    def query_past_experience(self, query: str, limit: int = 10) -> dict:
        """Federated Hot (FTS5) + Warm (SDR) search."""
        return self._call("query_past_experience", query=query, limit=limit)

    def patterns(self) -> dict:
        """Pattern detection across stored traces."""
        return self._call("patterns")
```

Estimated implementation: ~80 lines including the MCP-stdio client. Inline subprocess + JSON-RPC framing; no third-party MCP client needed.

---

## 7. Rule 35 — clarification needed

The spike surfaced an interpretive question that needs Joe's ratification before bridge code lands.

**Observed:** *every* read-side Harlo tool advances `exchange_index`. There is no zero-side-effect read.

**Strict reading of Rule 35** ("Hanna never writes to Harlo") would forbid any Harlo MCP call — making the bridge impossible.

**Proposed clarification:** Rule 35 means "Hanna never authors content into Harlo's trace store, never mutates Harlo's saved state, and never reconfigures Harlo's engine." The `exchange_index` counter advance is unavoidable telemetry that does not constitute a write in the architectural sense. The tools that DO constitute writes (and are forbidden to Hanna) are `store`, `stage_reload`, `resolve_verifications`, `trigger_cognitive_recalibration`.

**Edge case to resolve:** `coach` authors traces into Harlo's trace store (`recent-traces` accumulate from coach calls). Is calling `coach` from Hanna a Rule 35 violation? Two readings:

- **Strict:** yes — coach's "save" step writes to the trace store. Hanna's bridge must never call `coach`. Predictions and rich state reads are inaccessible to Hanna.
- **Permissive:** no — coach traces are observations of Hanna's existence in Harlo's session, not Hanna injecting content into Harlo's cognitive model. This is the only path to fresh predictions.

**Recommendation:** permissive reading, with the bridge explicit about it. `drive_coaching_exchange` is rate-limited (at most once per Hanna brief composition) and documented as "Hanna participates in a Harlo exchange to read fresh prediction; Harlo's record of this participation is observation, not authored content."

Either reading needs to be a ratified entry in `docs/DECISIONS.md` before bridge code lands. **Currently unresolved.**

---

## 8. Resolution of audit §12.5

**§12.5 (Harlo bridge contract reconciliation) — RESOLVED, pending one ratification.**

- v0.1.0 method names are kept (they describe Hanna's intent).
- v0.1.0 implementations are revised to call `status` (cheap) and `coach` (heavy), per §6.
- New method `drive_coaching_exchange` is added for the rare "drive fresh prediction" case.
- New method `read_schedule` falls out for free from the v9 envelope.
- Rule 35 interpretation re `coach` calls remains open (§7) — **the single blocker** before bridge code lands.

Other audit decisions affected:

- **§12.1 (Harlo state staleness TTL):** unblocked. `status` is cheap enough that polling at brief-composition cadence (~6× per workday) is trivial. 5-minute default TTL is fine; event-driven push is not needed.
- **§12.4 (predictor cold-start):** moot for now. Harlo's predictor is inactive (`engine.predictor: false`). `read_prediction()` returns None until Harlo flips that flag.
- **§4 XGBoost predictor status (Cut, pending ratification):** corroborated. There is nothing live to bootstrap from; a hand-coded heuristic is the only path forward until Harlo ships its predictor.

---

## 9. What's next

1. **Joe ratifies the Rule 35 reading of `coach`** in `docs/DECISIONS.md` — strict or permissive. This is the only blocker.
2. Bridge code lands following §6's contract.
3. The smaller day-zero PoC (§11.1) can then write `scripts/first_hanna_brief.py` using the real bridge end-to-end.

**No further spikes needed before first bridge code.**

---

## Appendix — raw response shapes (verbatim, sensitive content elided)

The five tool calls returned (in order): exchange_index 1 → 5. Schemas above were extracted from the responses. Trace content visible in `coach_block.recent-traces` is Joe's actual Harlo memory and is **deliberately not reproduced here**; only the envelope shape is captured. Schedule field read as `kind: "WORK"` during the spike (a Wednesday evening) — implying either an active override or a `/schedule/` prim authored to keep work hours open. Either way, the field is reliable for Hanna's lockout reads.

End of spike.
