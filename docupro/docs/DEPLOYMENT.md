# Deployment

DOCUPRO is one container: the API and the prebuilt web client are served from
the same origin. There is no database, no cache service and no object storage.

## 1. Docker Compose (recommended for a VPS)

```bash
cd docupro
cp .env.example .env        # adjust limits and retention
docker compose up -d --build
docker compose logs -f
```

The interface is on <http://localhost:8000>. The compose file already applies:

* non-root user (uid 10001),
* read-only root filesystem, `tmpfs` for `/tmp`,
* `no-new-privileges`, all capabilities dropped,
* `pids_limit: 256`, `mem_limit: 2g`, `cpus: 2.0`,
* a healthcheck on `/api/health`.

Put a TLS proxy in front of it. A ready-made Caddy configuration with automatic
HTTPS is in `deploy/Caddyfile`:

```bash
sudo cp deploy/Caddyfile /etc/caddy/Caddyfile   # edit the domain first
sudo systemctl reload caddy
```

`deploy/Caddyfile` raises the request body limit to 210 MB (above
`DOCUPRO_MAX_JOB_MB`) and forwards `X-Forwarded-Proto` so HSTS is applied.

## 2. Render (managed)

`render.yaml` is a Render Blueprint that builds `docupro/Dockerfile` and mounts a
1 GB disk at `/data`.

1. Push the repository to GitHub.
2. Render Dashboard → **New** → **Blueprint** → select the repository.
3. Render creates the `docupro` service from `render.yaml`.
4. Set `DOCUPRO_CORS_ORIGINS` if the interface is hosted on a different origin;
   otherwise leave it empty.

The **Starter** plan is required because free instances cannot attach a disk and
sleep after inactivity. Automatic deploys are disabled in the blueprint on
purpose: deployments go through `.github/workflows/deploy.yml`, which triggers
the deploy hook and then verifies the public URL.

To enable automated deployment, add these repository secrets:

| Secret | Value |
| --- | --- |
| `RENDER_DEPLOY_HOOK_URL` | Deploy Hook URL from the Render service settings |
| `DOCUPRO_PUBLIC_URL` | `https://docupro-xxxx.onrender.com` |

Then run **Actions → Deploy → Run workflow** and choose `render`. The workflow
triggers the deploy, waits for the health check and runs
`scripts/smoke_deploy.py` against the public URL. The last step is the evidence
that a deployment works; do not claim a deployment without it.

## 3. Fly.io

```bash
fly auth login
fly launch --no-deploy --config docupro/fly.toml --dockerfile docupro/Dockerfile
fly volumes create docupro_data --size 1 --region cdg
fly deploy --config docupro/fly.toml --dockerfile docupro/Dockerfile
fly open
```

`docupro/fly.toml` (create it from the example below) must mount the volume at
`/data` and set the same environment variables as `.env.example`.

```toml
app = "docupro"
primary_region = "cdg"

[build]
  dockerfile = "Dockerfile"

[env]
  DOCUPRO_DATA_DIR = "/data"
  DOCUPRO_WEB_DIR = "/app/web"

[[mounts]]
  source = "docupro_data"
  destination = "/data"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = "stop"
  auto_start_machines = true
  min_machines_running = 0

[[http_service.checks]]
  interval = "30s"
  timeout = "5s"
  grace_period = "15s"
  method = "GET"
  path = "/api/health"
```

Scale the VM to at least 2 shared CPUs and 2 GB RAM: one LibreOffice conversion
can use ~600 MB.

## 4. systemd + Caddy (own server)

```bash
sudo useradd --system --home /opt/docupro --shell /usr/sbin/nologin docupro
sudo rsync -a --exclude node_modules ./ /opt/docupro/
cd /opt/docupro && sudo python3 -m venv .venv
sudo .venv/bin/pip install -r services/api/requirements.txt
sudo -u docupro mkdir -p /var/lib/docupro
sudo install -d -m 750 /etc/docupro
sudo cp .env.example /etc/docupro/docupro.env   # edit it
sudo cp deploy/docupro.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now docupro
```

Build the interface once with `npm ci && npm run build` inside
`/opt/docupro/apps/web` and set `DOCUPRO_WEB_DIR=/opt/docupro/apps/web/dist`.
The unit runs uvicorn on `127.0.0.1:8000` with sandboxing enabled; Caddy
terminates TLS.

## 5. Container image from GitHub

`release.yml` publishes `ghcr.io/<owner>/docupro:<tag>` and `:latest` on every
`v*` tag. To run it:

```bash
docker run -d --name docupro -p 8000:8000 \
  -e DOCUPRO_DATA_DIR=/data -v docupro-data:/data \
  --read-only --tmpfs /tmp:size=512m \
  --security-opt no-new-privileges --cap-drop ALL \
  ghcr.io/<owner>/docupro:latest
```

## Environment variables

Everything is optional; defaults are production-sane. See `.env.example` for
the full annotated list. The most important ones:

| Variable | Default | Purpose |
| --- | --- | --- |
| `DOCUPRO_DATA_DIR` | `/tmp/docupro` | Job storage; must be writable and persistent |
| `DOCUPRO_WEB_DIR` | empty | Built web client; empty runs the API only |
| `DOCUPRO_MAX_UPLOAD_MB` | 50 | Per-file limit |
| `DOCUPRO_MAX_JOB_MB` | 200 | Per-job total |
| `DOCUPRO_RETENTION_MINUTES` | 30 | Output lifetime |
| `DOCUPRO_DELETE_AFTER_DOWNLOAD_SECONDS` | 120 | Early deletion after download |
| `DOCUPRO_MAX_CONCURRENCY` | 2 | Parallel conversions (≈1 per CPU) |
| `DOCUPRO_CONVERSION_TIMEOUT` | 240 | Wall clock per conversion |
| `DOCUPRO_RATE_LIMIT` | 40 | Requests per minute per client |
| `DOCUPRO_CORS_ORIGINS` | empty | Extra allowed origins (comma separated) |
| `DOCUPRO_TRUST_PROXY` | 1 | Use `X-Forwarded-For` for rate limiting |

## Operating notes

* **Scaling.** Job state is in memory. Do not run multiple replicas against the
  same data directory; scale vertically (`DOCUPRO_MAX_CONCURRENCY`) instead.
* **Disk.** Budget `2 ×` the largest expected upload per concurrent job.
  Compose mounts a named volume; Render mounts a disk; Fly uses a volume.
* **Monitoring.** `GET /api/health` for liveness, `GET /api/ready` for
  readiness (storage + queue), `GET /api/jobs` for queue counters.
* **Backups.** There is nothing to back up: documents are transient by design.
  Back up configuration (`.env`) and the image tag you deployed.
* **Upgrades.** Pull the new image, restart the container. Directories orphaned
  by the restart are removed automatically after 60 seconds.
