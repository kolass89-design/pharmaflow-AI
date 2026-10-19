# Continuous integration workflows

These files are ready to run but **cannot be pushed from the build environment
that produced this repository**: the GitHub App token used there is not granted
the `workflows` permission, and GitHub rejects any push that creates
`.github/workflows/*` (error recorded in the delivery report).

The workflows are stored here so they are versioned and reviewable. Activate
them with one command from the repository root:

```bash
docupro/scripts/install_workflows.sh          # copies ci/workflows/*.yml
git add .github/workflows && git commit -m "ci: activate pipelines" && git push
```

Requirements for the person pushing: a normal collaborator account or a token
with the `workflow` scope.

| Workflow | Trigger | What it actually does |
| --- | --- | --- |
| `ci.yml` | every push / PR | ruff lint + format check, pytest with coverage, engine verification of all conversions with Tesseract and LibreOffice installed, web type-check, production build, jsdom UI flow test against a live server, container build + real conversion inside the container, catalog contract check. |
| `release.yml` | tag `v*` | builds the web bundle, Windows NSIS/MSI installers (Rust + WebView2), Android APK and AAB (JDK 17, NDK 26), pushes a container image to GHCR, and publishes a GitHub release with SHA-256 checksums. |
| `deploy.yml` | manual | triggers a Render deploy hook or Fly.io deploy, then verifies the public URL end to end with `scripts/smoke_deploy.py`. |
| `security.yml` | weekly / dependency changes | `pip-audit --strict` and `npm audit --audit-level=high`. |

Secrets expected by `release.yml` / `deploy.yml` are documented in
`docs/DEPLOYMENT.md`; none of them are committed.
