# ADR-003: Access Protection — Single Passphrase, argon2 Hash, Signed Session Cookie

## Status

Accepted (2026-07-22; mechanism per DISCUSS OQ-1 resolution: passphrase, no accounts)

## Context

Public production URL holding one person's weight data. v1 is single-user, no accounts (locked); multi-user is a possible future — do not paint into a corner, do not build for it. Login friction must not violate the ≤5 s morning entry budget (US-006).

## Decision

One shared passphrase. Server holds only `PASSPHRASE_HASH` (argon2id, via argon2-cffi) as a Fly secret. Login: POST passphrase → verify → set signed HttpOnly SameSite=Lax cookie (itsdangerous, `SESSION_SIGNING_KEY` secret), 90-day expiry. `AccessGate` middleware guards every route except `/login` and health endpoint. Login attempts rate-limited (in-process token bucket — single instance makes this sufficient). Startup probe: both secrets present and parseable, else refuse to start. All traffic HTTPS (Fly edge TLS).

## Alternatives Considered

- **HTTP Basic Auth**: Rejected. Credentials replayed on every request; poor mobile UX (browser dialog, no styling, awkward with PWA install); no server-side expiry control.
- **Full account system (username/password, sessions table)**: Rejected. Explicitly out of scope for v1 (OQ-1 resolution); disproportionate build cost against the 5-day budget. Future path preserved: `AccessGate` is a middleware boundary — swapping passphrase verification for account-based auth later touches one component, no data-model change needed now.
- **OAuth/OIDC via external IdP**: Rejected. Third-party dependency, consent screens on a half-awake morning, and an external integration requiring contract maintenance — all for one user.
- **IP allowlist / VPN (Tailscale)**: Rejected. Breaks the "tap icon on any network" flow; phone IPs are dynamic.

## Consequences

- Positive: zero credentials stored beyond one hash; login roughly once per quarter per device (90 d) keeps the entry flow at zero auth friction; stateless sessions (no session table).
- Negative: one shared secret — rotation requires re-login on all devices (acceptable: one user); signed-cookie revocation is expiry-only (mitigation: rotate `SESSION_SIGNING_KEY` to force global logout). Session lifetime 90 d awaits user confirmation (open question to DISTILL).
