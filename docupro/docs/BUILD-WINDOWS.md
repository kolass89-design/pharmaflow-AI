# Windows build

The Windows application is a Tauri v2 shell around the same interface as the web
app. It is not a screenshot-in-a-window wrapper: it registers native dialogs
(`tauri-plugin-dialog`), native file writing (`tauri-plugin-fs`), external link
opening and Windows drag-and-drop.

## Prerequisites

* Windows 10/11 x64 (or Windows Server 2019+)
* Rust stable (MSVC toolchain) — <https://rustup.rs>
* Node.js 20 or 22
* Visual Studio Build Tools with "Desktop development with C++"
* WebView2 runtime (preinstalled on Windows 11 and current Windows 10; the
  installer is configured to download it if missing)

## Build

```powershell
cd docupro\apps\web
npm ci
npm run build

cd ..\desktop
npm install
npm run build:windows
```

Artifacts:

| File | Purpose |
| --- | --- |
| `src-tauri\target\release\bundle\nsis\DOCUPRO_1.0.0_x64-setup.exe` | Installer (per-user, no admin prompt) |
| `src-tauri\target\release\bundle\msi\DOCUPRO_1.0.0_x64_en-US.msi` | MSI for managed deployment |
| `src-tauri\target\release\docupro.exe` | Portable executable (run from any folder) |

The portable executable needs the WebView2 runtime, which is present on current
Windows versions.

## Pointing the app at your service

```powershell
$env:VITE_API_BASE = "https://docupro.example.com"
npm run build:windows
```

If no URL is baked in, users set it in **Settings → Conversion service** on first
launch, and the app explains that a running DOCUPRO service is required.

## Code signing (optional)

Unsigned installers trigger a SmartScreen warning; that is expected. To sign:

```powershell
$env:TAURI_SIGNING_PRIVATE_KEY = Get-Content -Raw .\docupro.key
$env:TAURI_SIGNING_PRIVATE_KEY_PASSWORD = "…"
npm run build:windows
```

Never commit `docupro.key`. In CI, provide it as the `TAURI_SIGNING_PRIVATE_KEY`
secret; the workflow only signs when the secret exists.

## How CI produces the release artifacts

`ci/workflows/release.yml` → job `windows`:

1. `actions/setup-node` + `dtolnay/rust-toolchain` + Rust cache
2. `npm ci` in `apps/web`, `npm install` in `apps/desktop`
3. `npm run build:windows` with `VITE_API_BASE` from the repository variable
   `DOCUPRO_API_BASE`
4. NSIS `.exe` and `.msi` are collected and attached to the GitHub release,
   together with a `SHA256SUMS.txt` file.

## Verifying a build

```powershell
Get-FileHash .\DOCUPRO_1.0.0_x64-setup.exe -Algorithm SHA256
.\DOCUPRO_1.0.0_x64-setup.exe      # installs per-user, then launch DOCUPRO
```

Then convert a file and use **Save as** — the native Windows dialog must appear,
which proves the shell (not the browser) handled the save.
