# Android build

The Android application uses the same Tauri v2 shell as Windows. Files are
picked with the native Android document picker (the standard file input, handled
by Tauri's WebView), results are saved through the native save dialog, and the
system share sheet can send a file to DOCUPRO.

## Prerequisites

* JDK 17 (`temurin-17` is used in CI)
* Android SDK with platform 34 and build tools 34.0.0
* Android NDK 26.1.10909125
* Rust with the four Android targets:
  ```bash
  rustup target add aarch64-linux-android armv7-linux-androideabi \
                    i686-linux-android x86_64-linux-android
  ```
* Node.js 20 or 22

Environment:

```bash
export ANDROID_HOME="$HOME/Android/Sdk"
export NDK_HOME="$ANDROID_HOME/ndk/26.1.10909125"
```

## Build

```bash
cd docupro/apps/web && npm ci && npm run build
cd ../desktop && npm install
npx tauri android init --ci          # generates src-tauri/gen/android (not committed)

export VITE_API_BASE="https://docupro.example.com"
npx tauri android build --apk --aab --ci
```

Outputs:

| File | Purpose |
| --- | --- |
| `src-tauri/gen/android/app/build/outputs/apk/universal/release/app-universal-release-unsigned.apk` | Universal APK (unsigned unless a keystore is configured) |
| `src-tauri/gen/android/app/build/outputs/bundle/universalRelease/app-universal-release.aab` | Play Store bundle |

Without a keystore these files are **unsigned** and cannot be installed on a
device. For an installable test build use a debug APK:

```bash
npx tauri android build --apk --debug
adb install -r src-tauri/gen/android/app/build/outputs/apk/universal/debug/app-universal-debug.apk
```

## Signing

Create a keystore once (keep it out of the repository):

```bash
keytool -genkeypair -v -keystore docupro-release.jks -alias docupro \
  -keyalg RSA -keysize 4096 -validity 10000
```

Provide it to the build with the environment variables that Tauri reads:

```bash
export TAURI_SIGNING_PRIVATE_KEY="$(base64 -w0 docupro-release.jks)"
export TAURI_SIGNING_PRIVATE_KEY_PASSWORD="…"
export ANDROID_KEY_ALIAS=docupro
```

In GitHub Actions, store the base64 keystore and the password as secrets and
restore them to `$RUNNER_TEMP` inside the workflow. Nothing is committed.

## How CI produces the release artifacts

`ci/workflows/release.yml` → job `android`:

1. Temurin JDK 17, Rust with all Android targets, SDK/NDK packages
2. `npm --prefix apps/web ci` and `npm --prefix apps/desktop install`
3. `npx tauri android init --ci` and `npx tauri android build --apk --aab --ci`
4. APK and AAB are attached to the GitHub release with checksums

## What the app does on a phone

* Pick a document from Files, Drive, Downloads or another app.
* Upload to the configured DOCUPRO service, watch real progress, cancel.
* Download the result to the folder chosen in the native save dialog.
* Works on Android 8.0 (API 26) and newer; the WebView must be reasonably
  current (System WebView updates itself through the Play Store).

## Verification checklist

- [ ] `adb install -r app-universal-debug.apk` succeeds
- [ ] The app opens the file picker and lists PDFs/images
- [ ] A conversion completes and the native save dialog appears
- [ ] Rotating the device does not lose the completed result
- [ ] Back button follows in-app history (React Router) instead of closing
