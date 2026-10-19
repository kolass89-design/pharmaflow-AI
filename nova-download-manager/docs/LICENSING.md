# Licensing

Nova Download Manager's own code is **MIT** licensed.

## Third-party components

| Component | Used for | License |
|---|---|---|
| Electron (Chromium + Node.js) | Desktop shell & media playback | MIT (Electron); Chromium: BSD-style + others (see `LICENSES.chromium.html` shipped inside Electron distributions) |
| React, React DOM | Desktop UI | MIT |
| Vite, esbuild, TypeScript, Vitest | Build/test tooling | MIT / Apache-2.0 (TypeScript) |
| OkHttp (Square) | Android HTTP engine | Apache-2.0 |
| Jetpack Compose / AndroidX | Android UI | Apache-2.0 |
| Media3 (ExoPlayer) | Android playback | Apache-2.0 |
| Kotlinx Coroutines | Android concurrency | Apache-2.0 |
| adm-zip | Extension packaging (build-time only) | MIT |
| jsdom | Extension tests (dev only) | MIT |

Notes:
- No FFmpeg binaries are bundled in 0.1.0. If transcoding is added later, an LGPL-configured FFmpeg build will be used with corresponding notices and source offers.
- Playback of patented codecs depends on the codecs provided by the host OS/Chromium/ExoPlayer build; Nova ships no additional codec implementations.
- "Nova Download Manager" is an original name/brand for this project. It is not affiliated with Tonec Inc. (Internet Download Manager) or any streaming platform.

If you redistribute Nova, keep this file and include the third-party licenses above (they are bundled in `node_modules` / Gradle dependency metadata and inside Electron distributions as applicable).
