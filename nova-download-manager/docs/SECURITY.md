# Nova — Security model

## Principles

Nova has **no backend, no accounts, and no telemetry**. Everything (history, settings, partial files) is stored locally. There is deliberately no server-side download proxy: files move directly between the origin server and the user's device.

## Network safety

- Only `http:`/`https:` URLs are downloadable (no `file:`, `ftp:`, `javascript:`, etc.).
- **Private-network guard:** by default, URLs pointing to loopback, RFC-1918, link-local, CGNAT, `localhost` or `*.local` are rejected. This prevents links from web pages/extensions/clipboard being used to probe the user's LAN or hit local admin interfaces/cloud metadata (`169.254.169.254`). Users can opt out in Settings for trusted local servers.
  - *Known limitation:* the check evaluates the literal host in the URL. A public hostname that *resolves* to a private IP (DNS rebinding) is not re-checked after DNS — a deliberate trade-off for a desktop downloader (it also must allow CDNs). The bridge token requirement still applies before any download starts.
- Redirects (≤10) are followed manually so every hop is re-validated with the same rules.
- TLS certificate errors abort the download with a clear message; there is no "ignore certificate" option.
- HTTP 401/403 stop immediately. Nova never sends browser cookies, never harvests sessions, and never attempts to bypass authentication, DRM, paywalls or rate limits (429s are backed off from, honoring `Retry-After`).

## Filesystem safety

- Server-supplied filenames are sanitized: directory components stripped (POSIX + Windows separators), control/illegal characters replaced, Windows reserved device names neutralized, trailing dots/spaces trimmed, length capped. Downloads can never escape the chosen destination folder via `../`.
- Partial data uses `.novapart` / `.nova-meta.json` sidecars; final files appear only after byte-count validation (and SHA-256 verification when the server publishes a checksum).
- **Downloaded programs are never executed automatically.** "Open" on an executable reveals it in the file manager (desktop) or requires an explicit trust confirmation (Android), so users can antivirus-scan first.
- URLs shown in errors/logs have credentials redacted.

## Browser bridge (desktop ↔ extension)

- Binds `127.0.0.1` only. Mutations require a per-install 192-bit random token (constant-time comparison), displayed in-app and entered in the extension once.
- CORS responses are only granted to `chrome-extension://`/`moz-extension://`/`edge-extension://` origins, so arbitrary websites cannot read responses — and without the token they cannot queue anything either.
- Payloads capped at 64 KB; URLs re-validated by the engine. The only unauthenticated endpoint, `GET /ping`, reveals just that Nova is running.
- The token can be regenerated at any time; the bridge can be disabled entirely.

## Extension permissions (and why)

| Permission | Why |
|---|---|
| `activeTab` + `scripting` | On-demand "Scan this page" when the user clicks |
| `contextMenus` | "Download with Nova" right-click actions |
| `storage` | Token/settings in the browser only |
| host `http://127.0.0.1/*` | Talk to the local Nova app |
| *optional* `*://*/*` | Only when the user enables automatic detection; granted via the browser prompt and used solely to register the detector |

The detector inspects only media/link element attributes — never page text, forms, history, or cookies — and sends candidates only to the user's own Nova app.

## Reporting issues

Please open a GitHub issue with reproduction steps (do not include private URLs/tokens). For sensitive reports, contact the maintainer privately first.

## Out of scope (by design)

Nova is not an antivirus. Keep OS protections (SmartScreen/Gatekeeper/Play Protect) and your antivirus enabled, and only download files from sources you trust. Any downloadable file can be malicious.
