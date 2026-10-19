# Building Nova from source

## Prerequisites

| Component | Needs |
|---|---|
| Core + extension | Node.js ≥ 20 |
| Desktop | Node ≥ 20; packaging downloads the Electron runtime (~110 MB) |
| Android | JDK 17, Android SDK (API 34), Gradle 8.9 (`gradle` on PATH or Android Studio) |

## Quick start

```bash
npm install
npm run build -w @nova/core
npm test                                  # engine + bridge + detection suites
npm run build -w @nova/desktop            # dist/ (renderer) + dist-electron/
npm run zip -w @nova/extension            # apps/extension/nova-extension.zip
```

Run the desktop app in dev:

```bash
cd apps/desktop
npm run dev        # Vite renderer on http://127.0.0.1:5173 (browser preview w/ demo data)
# in another terminal, with the real bridge:
VITE_DEV_SERVER_URL=http://127.0.0.1:5173 npm start   # Electron shell
```

## Packaging

```bash
npm run dist:win -w @nova/desktop     # apps/desktop/release/*.exe (NSIS + portable)
npm run dist:linux -w @nova/desktop   # *.AppImage, *.tar.gz
cd apps/android && gradle assembleRelease bundleRelease
# -> app/build/outputs/apk/release/app-release.apk
# -> app/build/outputs/bundle/release/app-release.aab
```

Windows binaries can be cross-built from Linux/macOS (electron-builder); `signAndEditExecutable` is disabled in the config so no Wine/rcedit is needed.

## Signing

- **Windows:** set `CSC_LINK` (path/URL to .pfx) + `CSC_KEY_PASSWORD` before `dist:win` for signed installers. Without them builds are unsigned (SmartScreen warning).
- **Android:** set env `NOVA_KEYSTORE_FILE`, `NOVA_KEYSTORE_PASSWORD`, `NOVA_KEY_ALIAS`, `NOVA_KEY_PASSWORD`. Without them the release build is signed with the **debug key** (installable, but not publishable).

## CI (GitHub Actions)

- `release.yml` (repo root of the standalone project) builds + tests everything on `v*` tags and publishes a GitHub Release with the Windows/Android/Linux/extension artifacts.
- Optional CI secrets: `NOVA_KEYSTORE_BASE64` (base64 of the .jks), `NOVA_KEYSTORE_PASSWORD`, `NOVA_KEY_ALIAS`, `NOVA_KEY_PASSWORD`. Create a keystore once:
  `keytool -genkeypair -v -keystore nova-release.jks -alias nova -keyalg RSA -keysize 2048 -validity 10000`

⚠️ Never commit keystores, certificates, tokens, or passwords to Git. `.gitignore` excludes common cases, but stay vigilant.

## Troubleshooting

- **Electron postinstall fails (cert/network):** run `npm install --ignore-scripts` for development/tests, and let CI (or a machine with unrestricted access to GitHub release assets) do packaging.
- **Bridge port in use:** change it in Nova → Settings and in the extension options (default 47117).
- **Android build wants SDK location:** set `sdk.dir` in `apps/android/local.properties` or `ANDROID_HOME`.

## What CI verifies on every run

1. `npm ci` + TypeScript typecheck (desktop renderer/main, extension).
2. Full test suites (54 tests at time of writing).
3. Extension zip build.
4. Platform packaging: Windows (windows-latest), Linux, Android (with SDK 34).
