# Enabling CI

## Standalone `nova-download-manager` repository (recommended)

Nothing to do — `.github/workflows/release.yml` in this project root already
tests and builds Windows/Linux/Android + the extension, and publishes a
GitHub Release when you push a tag such as `v0.1.0`.

## While Nova lives inside another repository (e.g. this monorepo)

GitHub only runs workflows from the **repository root** `.github/workflows/`.
Copy `nova-ci.root-workflow.yml` (this folder) to `.github/workflows/nova-ci.yml`
at the root of the host repository and commit **with an account that has
workflow permissions**. It triggers on pushes that touch `nova-download-manager/**`
on the development branch, and manually via *Actions → Run workflow*.

Why wasn't it committed directly? The automated development environment's
GitHub App token has contents access but not the `workflows` permission —
both `git push` and the Contents API refuse to create root workflow files
(`403 Resource not accessible by integration`). Adding it via the GitHub web
UI ("Add file") with your own account takes under a minute.
