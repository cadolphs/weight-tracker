# ADR-001: Stack and Hosting — Python/FastAPI Monolith on Fly.io

## Status

Accepted (2026-07-22, user-selected from DESIGN options)

## Context

Greenfield single-user mobile-first web app; ~5 dev days total; solo developer (Python-comfortable); operational simplicity and near-zero hosting cost are explicit constraints; durability guardrail (confirmed save never lost); walking skeleton must reach production day 1. The domain's hard part (trend math, validation) is pure logic best served by strong test tooling.

## Decision

Single deployable: Python 3.12 + FastAPI + uvicorn, Jinja2 server-rendered pages + vanilla JS + uPlot (MIT, ~45 kB) for charts, PWA manifest + minimal service worker for Android home-screen install. Hosted on Fly.io shared-cpu-1x with a 1 GB volume (~$2–3/mo). Deployed via `fly deploy` (Dockerfile), optionally from GitHub Actions.

## Alternatives Considered

- **Option B — SvelteKit on Cloudflare Workers + D1 ($0/mo)**: Rejected. D1 diverges from local SQLite semantics (worse local/prod parity), persistence is vendor-runtime-coupled and cannot be probed directly (Earned Trust), and an SSR framework adds moving parts for a 5-page app. Zero cost did not outweigh probe-ability and parity.
- **Option C — Go monolith on Hetzner VPS (~€4/mo)**: Rejected. Functionally equivalent but adds ongoing ops burden (OS patching, TLS, backup babysitting) with no functional gain; second language for no reason given developer's Python fluency.
- **Static SPA + browser storage ($0)**: Rejected. Fails the durability guardrail (device loss/cache eviction = data loss) and complicates the passphrase gate.

## Consequences

- Positive: one language end-to-end; pure-core trend testable with pytest + Hypothesis; identical SQLite semantics locally and in prod; all OSS (MIT/BSD/Apache); ops ≈ zero.
- Negative: ~$2–3/mo (vs $0 for Option B); single-region single VM (acceptable: one user, Litestream covers host loss per ADR-002); Fly platform dependency (mitigated: plain Dockerfile + SQLite file are portable anywhere).
