# 0001: Deploy both services to Fly.io

## Status
Accepted

## Context
`docs/HANDOFF.md` §1.1 originally proposed Google Cloud Run for `brain` and a VM or
Fly.io/Render for `pipeline`, because `pipeline` holds a long-lived WebSocket per call and
Cloud Run's request model historically fit that poorly. That split means learning and
configuring two different platforms for a two-person team.

## Decision
Deploy both `brain` and `pipeline` to Fly.io, as two separate apps (`fly.brain.toml`,
`fly.pipeline.toml`). Both get `auto_stop_machines = false` and `min_machines_running = 1` so
neither cold-starts mid-call. `pipeline` reaches `brain` over Fly's private 6PN network
(`callmate-brain.internal`) rather than brain's public URL, since only `pipeline` needs to
reach it.

## Why
- One platform, one CLI (`flyctl`), one mental model — less setup overhead than Cloud Run +
  a second platform for a small team.
- Fly's `[http_service]` transparently passes through WebSocket upgrades, so `pipeline`'s
  long-lived WS doesn't need special handling.
- Fly's private networking keeps `brain` off the public internet by default, which Cloud Run
  would need extra IAM/VPC configuration to achieve.

## Consequences
- The database is Neon (external managed Postgres+pgvector), not Fly Postgres — neither
  service needs Fly's own Postgres offering.
- `docs/HANDOFF.md` §1.1's "Deploy (demo)" row is superseded by this ADR for the actual
  deployment target; update that row if this decision is revisited.
