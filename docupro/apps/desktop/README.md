# DOCUPRO desktop & mobile shell (Tauri v2)

This shell wraps the shared DOCUPRO web interface in a native window on Windows
and a native activity on Android. It is **not** a generic WebView wrapper: it
registers native file dialogs, native file writing (Save As), external link
opening and the platform back button, and it packages the interface locally so
the app starts instantly without a browser.

## Why Tauri

* ~3–6 MB installer instead of ~120 MB for Electron.
* Uses the operating system webview (WebView2 on Windows, Android System
  WebView), so memory use stays low on modest hardware.
* Rust core with a minimal, explicitly granted permission set.
* One codebase for Windows and Android, with the conversion engine shared
  through the same HTTP API as the web app.

## Pointing the app at a conversion service

The interface calls the conversion API over HTTPS. Set the service URL at build
time:

```bash
export VITE_API_BASE="https://your-docupro-service.example.com"
```

Users can also change it at runtime in **Settings → Conversion service**. On
first launch without a configured URL, the app explains that a service URL is
required.

## Windows build

```bash
cd apps/desktop
npm install
npm run build:windows      # NSIS setup + MSI, unsigned unless configured
```

Artifacts appear in `src-tauri/target/release/bundle/nsis` and `.../msi`.
Signing is optional; see `docs/BUILD-WINDOWS.md`. Unsigned installers trigger a
SmartScreen warning, which is expected and explained in the installation guide.

## Android build

```bash
cd apps/desktop
npm install
npm run init:android       # requires JDK 17 + Android SDK/NDK
npm run build:android -- --apk --aab
```

The generated Gradle project lives in `src-tauri/gen/android` and is created by
the Tauri CLI, so it is not committed. Signing is configured with the
`DOCUPRO_ANDROID_*` environment variables documented in
`docs/BUILD-ANDROID.md`. The CI workflow performs the same steps on a clean
machine for every release.

## Icons

`src-tauri/icons/source.png` is the 1024 px master. Regenerate every platform
icon with:

```bash
npm run icons
```
