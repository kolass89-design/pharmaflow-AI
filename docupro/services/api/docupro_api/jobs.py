"""Asynchronous job management.

Each conversion runs in its own short-lived OS process. That gives real
timeouts, real cancellation, crash isolation and memory reclamation without
introducing a broker or a database. Jobs live on disk under a private data
directory and are removed automatically by a sweeper thread.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .config import Settings
from .errors import (
    ApiError,
    ConversionFailed,
    NotFound,
    QueueFull,
    ValidationError,
)
from .security import sanitize_filename

log = logging.getLogger(__name__)

STATUS_QUEUED = "queued"
STATUS_RUNNING = "running"
STATUS_SUCCEEDED = "succeeded"
STATUS_FAILED = "failed"
STATUS_CANCELLED = "cancelled"
STATUS_EXPIRED = "expired"

TERMINAL = {STATUS_SUCCEEDED, STATUS_FAILED, STATUS_CANCELLED, STATUS_EXPIRED}


@dataclass
class UploadedSource:
    path: Path
    original_name: str
    safe_name: str
    kind: str
    size: int
    pages: int | None = None


@dataclass
class Job:
    id: str
    tool: str
    token: str
    status: str
    options: dict[str, Any]
    inputs: list[dict[str, Any]]
    created_at: float
    expires_at: float
    root: Path
    max_seconds: int
    progress: float = 0.0
    message: str = ""
    error: dict[str, Any] | None = None
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    started_at: float | None = None
    finished_at: float | None = None
    process: subprocess.Popen | None = None
    downloaded: set[str] = field(default_factory=set)
    cancel_requested: bool = False
    forced_error: dict[str, Any] | None = None
    deleted: bool = False
    lock: threading.Lock = field(default_factory=threading.Lock)

    @property
    def input_dir(self) -> Path:
        return self.root / "input"

    @property
    def work_dir(self) -> Path:
        return self.root / "work"

    @property
    def output_dir(self) -> Path:
        return self.root / "output"

    def public(self) -> dict[str, Any]:
        now = time.time()
        remaining = max(0, int(self.expires_at - now)) if self.status == STATUS_SUCCEEDED else None
        artifacts = []
        if self.status == STATUS_SUCCEEDED:
            for artifact in self.artifacts:
                entry = dict(artifact)
                entry["url"] = f"/api/jobs/{self.id}/download/{artifact['id']}?token={self.token}"
                artifacts.append(entry)
        return {
            "id": self.id,
            "tool": self.tool,
            "status": self.status,
            "progress": round(self.progress, 3),
            "message": self.message,
            "createdAt": self.created_at,
            "startedAt": self.started_at,
            "finishedAt": self.finished_at,
            "expiresAt": self.expires_at if self.status == STATUS_SUCCEEDED else None,
            "expiresInSeconds": remaining,
            "inputs": self.inputs,
            "artifacts": artifacts,
            "error": self.error,
            "meta": self.meta,
            "warnings": self.warnings,
            "options": {
                k: ("••••••" if k in {"password", "owner_password"} and v else v) for k, v in self.options.items()
            },
        }


class JobManager:
    def __init__(self, settings: Settings, spec_lookup: Callable[[str], Any]) -> None:
        self.settings = settings
        self._spec_lookup = spec_lookup
        self._jobs: dict[str, Job] = {}
        self._lock = threading.RLock()
        self._active = 0
        self._slots = threading.Semaphore(settings.max_concurrent_jobs)
        self._stop = threading.Event()
        self._sweeper = threading.Thread(target=self._sweep_loop, name="docupro-sweeper", daemon=True)
        self._sweeper.start()
        self._cleanup_orphans()

    # -- lifecycle ---------------------------------------------------------
    def shutdown(self) -> None:
        self._stop.set()
        with self._lock:
            for job in self._jobs.values():
                if job.process and job.process.poll() is None:
                    job.cancel_requested = True
                    try:
                        job.process.terminate()
                    except OSError:
                        pass

    def _cleanup_orphans(self) -> None:
        """Remove job directories left behind by a previous process."""
        try:
            for entry in self.settings.jobs_dir.iterdir():
                if entry.is_dir() and entry.name not in self._jobs:
                    age = time.time() - entry.stat().st_mtime
                    if age > 60:
                        shutil.rmtree(entry, ignore_errors=True)
        except OSError:  # pragma: no cover
            pass

    def _sweep_loop(self) -> None:
        while not self._stop.wait(self.settings.sweep_interval_seconds):
            try:
                self.sweep()
            except Exception:  # pragma: no cover - never kill the sweeper
                log.exception("Sweeper iteration failed")

    def sweep(self) -> None:
        now = time.time()
        expired: list[Job] = []
        with self._lock:
            for job in list(self._jobs.values()):
                if job.status in {STATUS_QUEUED, STATUS_RUNNING}:
                    if job.cancel_requested:
                        continue
                    if job.started_at and now - job.started_at > job.max_seconds + 30:
                        job.forced_error = {
                            "code": "conversion_timeout",
                            "message": "The conversion took too long and was stopped.",
                        }
                        self._terminate(job)
                    continue
                if now >= job.expires_at and not job.deleted:
                    expired.append(job)
        for job in expired:
            self._expire(job)

    def _expire(self, job: Job) -> None:
        with job.lock:
            job.deleted = True
            job.status = STATUS_EXPIRED
            job.artifacts = []
            job.error = {"code": "expired", "message": "The files have been deleted according to the retention policy."}
            shutil.rmtree(job.output_dir, ignore_errors=True)
            shutil.rmtree(job.input_dir, ignore_errors=True)
            shutil.rmtree(job.work_dir, ignore_errors=True)
        log.info("Job %s expired and was cleaned", job.id[:8])

    # -- submission --------------------------------------------------------
    def reserve(self, tool: str, options: dict[str, Any]) -> Job:
        """Create a job record and its private directories before uploads land."""
        spec = self._spec_lookup(tool)
        if spec is None:
            raise ValidationError("Unknown tool.", code="unknown_tool")
        with self._lock:
            queued = sum(1 for j in self._jobs.values() if j.status in {STATUS_QUEUED, STATUS_RUNNING})
            if queued >= self.settings.max_queue:
                raise QueueFull(
                    "The conversion queue is full. Please wait a moment and try again.",
                    code="queue_full",
                )
            job_id = uuid.uuid4().hex
            token = uuid.uuid4().hex
            now = time.time()
            root = self.settings.jobs_dir / job_id
            job = Job(
                id=job_id,
                tool=tool,
                token=token,
                status=STATUS_QUEUED,
                options=options,
                inputs=[],
                created_at=now,
                expires_at=now + max(300, self.settings.conversion_timeout + 120),
                root=root,
                max_seconds=self.settings.conversion_timeout,
                message="Receiving files",
                progress=0.01,
            )
            self._jobs[job_id] = job
        try:
            job.root.mkdir(parents=True, exist_ok=False, mode=0o700)
            job.input_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        except OSError as exc:  # pragma: no cover - disk failure
            with self._lock:
                self._jobs.pop(job_id, None)
            raise ConversionFailed("Temporary storage is unavailable on the server.") from exc
        return job

    def enqueue(self, job: Job, sources: list[UploadedSource]) -> Job:
        """Start the worker for a fully uploaded job."""
        spec = self._spec_lookup(job.tool)
        if spec is None:
            self.delete(job.id)
            raise ValidationError("Unknown tool.", code="unknown_tool")
        with job.lock:
            job.inputs = [{"name": s.original_name, "size": s.size, "pages": s.pages, "kind": s.kind} for s in sources]
            job.message = "Waiting for a worker"
            job.progress = 0.02
        job.output_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        job.work_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        manifest = {
            "job_id": job.id,
            "tool": job.tool,
            "options": job.options,
            "sources": [
                {
                    "path": str(s.path),
                    "original_name": s.original_name,
                    "safe_name": s.safe_name,
                    "kind": s.kind,
                    "size": s.size,
                    "pages": s.pages,
                    "order": index,
                }
                for index, s in enumerate(sources)
            ],
            "output_dir": str(job.output_dir),
            "work_dir": str(job.work_dir),
            "max_pages": self.settings.max_pages,
            "max_pixels": self.settings.max_pixels,
            "max_upload_bytes": self.settings.max_upload_bytes,
            "max_job_bytes": self.settings.max_job_bytes,
        }
        (job.root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        threading.Thread(target=self._run, args=(job,), name=f"job-{job.id[:8]}", daemon=True).start()
        return job

    # -- execution ---------------------------------------------------------
    def _run(self, job: Job) -> None:
        with self._slots:
            self._run_guarded(job)

    def _run_guarded(self, job: Job) -> None:
        with job.lock:
            if job.cancel_requested:
                job.status = STATUS_CANCELLED
                job.finished_at = time.time()
                job.expires_at = job.finished_at
                return
            job.status = STATUS_RUNNING
            job.started_at = time.time()
            job.message = "Starting engine"
            job.progress = 0.05
        command = [
            sys.executable,
            "-m",
            "docupro_api.worker",
            str(job.root),
        ]
        env = {
            "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
            "HOME": str(job.work_dir),
            "TMPDIR": str(job.work_dir),
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "OMP_NUM_THREADS": "1",
            "PYTHONUNBUFFERED": "1",
            "PYTHONPATH": str(Path(__file__).resolve().parent.parent),
            "DOCUPRO_JOB_SECONDS": str(job.max_seconds),
            "DOCUPRO_MAX_PIXELS": str(self.settings.max_pixels),
            "DOCUPRO_MAX_PAGES": str(self.settings.max_pages),
            "TESSERACT_TIMEOUT": "60",
        }
        try:
            process = subprocess.Popen(
                command,
                cwd=str(job.root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
                bufsize=1,
            )
        except OSError as exc:  # pragma: no cover
            self._fail(job, ConversionFailed("The conversion worker could not be started."))
            log.error("Worker spawn failed: %s", exc)
            return
        with job.lock:
            job.process = process

        result_error: dict[str, Any] | None = None
        stderr_tail: list[str] = []
        deadline = time.time() + job.max_seconds
        started = time.time()

        def read_stderr() -> None:
            assert process.stderr is not None
            for line in process.stderr:
                stderr_tail.append(line.rstrip())
                if len(stderr_tail) > 40:
                    del stderr_tail[0]

        err_thread = threading.Thread(target=read_stderr, daemon=True)
        err_thread.start()

        assert process.stdout is not None
        try:
            for line in process.stdout:
                line = line.strip()
                if not line:
                    continue
                if not line.startswith("{"):
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                kind = event.get("type")
                if kind == "progress":
                    with job.lock:
                        fraction = float(event.get("fraction", job.progress))
                        job.progress = max(job.progress, min(0.99, fraction))
                        job.message = str(event.get("message", job.message))[:200]
                elif kind == "error":
                    result_error = {
                        "code": str(event.get("code", "conversion_failed")),
                        "message": str(event.get("message", "The conversion failed."))[:400],
                        "details": event.get("details") or {},
                    }
                elif kind == "result":
                    with job.lock:
                        job.artifacts = self._collect_artifacts(job, event.get("artifacts", []))
                        job.meta = event.get("meta") or {}
                        job.warnings = [str(w)[:300] for w in (event.get("warnings") or [])][:6]
                if time.time() > deadline or job.cancel_requested:
                    self._terminate(job)
                    break
            if job.cancel_requested:
                self._terminate(job)
                process.wait(timeout=10)
            else:
                process.wait(timeout=max(5, min(30, deadline - time.time() + 10)))
        except subprocess.TimeoutExpired:
            self._terminate(job)
            result_error = {"code": "conversion_timeout", "message": "The conversion timed out."}
        except Exception as exc:  # pragma: no cover - defensive
            self._terminate(job)
            result_error = {"code": "conversion_failed", "message": "The conversion worker failed unexpectedly."}
            log.exception("Worker supervision error for job %s: %s", job.id[:8], exc)
        finally:
            err_thread.join(timeout=2)

        elapsed = round(time.time() - started, 2)
        with job.lock:
            if job.cancel_requested:
                job.status = STATUS_CANCELLED
                job.error = {"code": "cancelled", "message": "The conversion was cancelled."}
                job.finished_at = time.time()
                job.progress = 0.0
                job.expires_at = job.finished_at
                self._remove_files(job)
                return
            job.meta = {**(job.meta or {}), "durationSeconds": elapsed}
            if job.forced_error is not None:
                result_error = job.forced_error
            if result_error is not None:
                self._fail_locked(job, result_error)
                return
            if not job.artifacts:
                self._fail_locked(
                    job,
                    {
                        "code": "conversion_failed",
                        "message": "The conversion finished without producing a downloadable file.",
                    },
                )
                return
            job.status = STATUS_SUCCEEDED
            job.progress = 1.0
            job.message = "Ready to download"
            job.finished_at = time.time()
            job.expires_at = job.finished_at + self.settings.retention_minutes * 60
        log.info(
            "Job %s (%s) %s in %.2fs",
            job.id[:8],
            job.tool,
            job.status,
            elapsed,
        )
        self._apply_post_success_policy(job)
        self.trim()

    def _collect_artifacts(self, job: Job, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        artifacts: list[dict[str, Any]] = []
        total = 0
        for index, entry in enumerate(raw[:100]):
            name = sanitize_filename(str(entry.get("filename", "download")), fallback="download")
            relative = str(entry.get("path", ""))
            candidate = (job.output_dir / Path(relative).name).resolve()
            if job.output_dir.resolve() not in candidate.parents:
                continue
            if not candidate.exists() or not candidate.is_file():
                continue
            size = candidate.stat().st_size
            if size <= 0:
                continue
            total += size
            if total > self.settings.max_job_bytes:
                raise ConversionFailed("The generated files exceed the allowed output size.")
            artifacts.append(
                {
                    "id": f"a{index + 1}",
                    "name": name,
                    "mediaType": str(entry.get("media_type", "application/octet-stream"))[:120],
                    "size": size,
                    "meta": entry.get("meta") or {},
                    "primary": bool(entry.get("is_primary", index == 0)),
                }
            )
        return artifacts

    def _apply_post_success_policy(self, job: Job) -> None:
        """Remove source uploads immediately; outputs follow the retention policy."""
        shutil.rmtree(job.input_dir, ignore_errors=True)

    def _terminate(self, job: Job) -> None:
        process = job.process
        if process and process.poll() is None:
            try:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            except OSError:  # pragma: no cover
                pass

    def _remove_files(self, job: Job) -> None:
        for sub in (job.input_dir, job.output_dir, job.work_dir):
            shutil.rmtree(sub, ignore_errors=True)

    def _fail(self, job: Job, exc: ApiError) -> None:
        with job.lock:
            self._fail_locked(job, {"code": exc.code, "message": exc.message, "details": exc.details})

    def _fail_locked(self, job: Job, error: dict[str, Any]) -> None:
        job.status = STATUS_FAILED
        job.error = error
        job.finished_at = time.time()
        job.progress = 0.0
        job.expires_at = job.finished_at + min(600, self.settings.retention_minutes * 60)
        self._remove_files(job)
        log.info("Job %s (%s) failed: %s", job.id[:8], job.tool, error.get("code"))

    # -- access ------------------------------------------------------------
    def get(self, job_id: str, token: str | None = None) -> Job:
        if not job_id or len(job_id) != 32:
            raise NotFound("This conversion could not be found. It may have expired.", code="job_not_found")
        with self._lock:
            job = self._jobs.get(job_id)
        if job is None:
            raise NotFound("This conversion could not be found. It may have expired.", code="job_not_found")
        if token is not None and token != job.token:
            raise NotFound("This conversion could not be found. It may have expired.", code="job_not_found")
        return job

    def cancel(self, job_id: str) -> Job:
        job = self.get(job_id)
        with job.lock:
            if job.status in TERMINAL:
                return job
            job.cancel_requested = True
            self._terminate(job)
            job.status = STATUS_CANCELLED
            job.message = "Cancelled"
            job.finished_at = time.time()
            job.expires_at = job.finished_at
            job.error = {"code": "cancelled", "message": "The conversion was cancelled."}
            self._remove_files(job)
        return job

    def delete(self, job_id: str) -> None:
        job = self.get(job_id)
        with job.lock:
            job.cancel_requested = True
            self._terminate(job)
            job.deleted = True
            self._remove_files(job)
            job.artifacts = []
            job.status = STATUS_EXPIRED
            job.error = {"code": "deleted", "message": "The files were deleted at your request."}
        log.info("Job %s deleted on request", job_id[:8])

    def artifact_for_download(self, job_id: str, artifact_id: str, token: str) -> tuple[Job, Path, dict[str, Any]]:
        job = self.get(job_id, token)
        if job.status != STATUS_SUCCEEDED:
            raise NotFound("These files are no longer available.", code="artifacts_gone")
        if time.time() > job.expires_at or job.deleted:
            raise NotFound("These files have expired and were deleted.", code="artifacts_expired")
        for artifact in job.artifacts:
            if artifact["id"] == artifact_id:
                path = job.output_dir / f"artifact-{artifact_id}"
                if not path.is_file():
                    raise NotFound("This file has already been removed.", code="artifacts_gone")
                return job, path, artifact
        raise NotFound("Unknown file for this conversion.", code="artifact_not_found")

    def register_download(self, job: Job, artifact_id: str) -> None:
        with job.lock:
            job.downloaded.add(artifact_id)
            ids = {a["id"] for a in job.artifacts}
            if ids and job.downloaded >= ids and self.settings.delete_after_download_seconds > 0:
                # Everything has been collected: shorten retention.
                job.expires_at = min(job.expires_at, time.time() + self.settings.delete_after_download_seconds)

    def stats(self) -> dict[str, Any]:
        with self._lock:
            jobs = list(self._jobs.values())
        counts = {
            status: 0
            for status in (
                STATUS_QUEUED,
                STATUS_RUNNING,
                STATUS_SUCCEEDED,
                STATUS_FAILED,
                STATUS_CANCELLED,
                STATUS_EXPIRED,
            )
        }
        for job in jobs:
            counts[job.status] = counts.get(job.status, 0) + 1
        return {
            "jobs": counts,
            "retained": len(jobs),
            "concurrency": self.settings.max_concurrent_jobs,
            "maxQueue": self.settings.max_queue,
        }

    def trim(self) -> None:
        """Keep the in-memory job table bounded."""
        with self._lock:
            finished = [j for j in self._jobs.values() if j.status in TERMINAL]
            if len(finished) <= self.settings.max_retained_jobs:
                return
            finished.sort(key=lambda j: j.finished_at or j.created_at)
            for job in finished[: len(finished) - self.settings.max_retained_jobs]:
                self._jobs.pop(job.id, None)
