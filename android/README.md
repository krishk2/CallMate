# android/ (optional, Phase 3)

`CallScreeningService` companion app: rejects non-contact callers in `screen_unknown` mode so
carrier "forward on busy" routes them to Twilio, plus a toggle for modes
(`docs/HANDOFF.md` §6.1.14).

Owned by Antigravity (`ANTIGRAVITY_HANDOFF.md` §1.7). Separate Kotlin codebase; only needs to
agree on the mode toggle it exposes via the brain's REST settings endpoint.
