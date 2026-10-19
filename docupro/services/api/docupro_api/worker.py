"""Conversion worker process.

Started by the job manager as ``python -m docupro_api.worker <job_dir>``.
It reads ``manifest.json``, runs exactly one conversion and reports progress
as JSON lines on stdout. It never receives user-controlled command arguments.
"""

from __future__ import annotations

import json
import os
import signal
import sys
import traceback
from pathlib import Path


def _limit_resources(max_seconds: int, max_bytes: int) -> None:
    try:
        import resource

        cpu = max_seconds + 20
        resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu + 10))
        resource.setrlimit(resource.RLIMIT_FSIZE, (max_bytes, max_bytes))
        resource.setrlimit(resource.RLIMIT_NOFILE, (1024, 1024))
    except Exception:  # pragma: no cover - not fatal on platforms without rlimit
        pass


def emit(event: dict) -> None:
    sys.stdout.write(json.dumps(event, default=str) + "\n")
    sys.stdout.flush()


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python -m docupro_api.worker <job_dir>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))

    from .config import Settings
    from .engines.models import ConversionContext, SourceFile
    from .engines.registry import get_spec
    from .errors import ApiError

    max_seconds = int(os.environ.get("DOCUPRO_JOB_SECONDS", "240"))
    _limit_resources(max_seconds, int(manifest.get("max_job_bytes", 200 * 1024 * 1024)))

    settings = Settings()
    spec = get_spec(manifest["tool"])
    if spec is None:
        emit({"type": "error", "code": "unknown_tool", "message": "Unknown conversion."})
        return 1

    sources = [
        SourceFile(
            path=Path(item["path"]),
            original_name=item["original_name"],
            safe_name=item["safe_name"],
            kind=item["kind"],
            size=int(item["size"]),
            pages=item.get("pages"),
            order=int(item.get("order", 0)),
        )
        for item in manifest["sources"]
    ]
    for source in sources:
        if not source.path.exists():
            emit(
                {
                    "type": "error",
                    "code": "invalid_file",
                    "message": "An uploaded file was missing before processing.",
                }
            )
            return 1

    cancelled = {"value": False}

    def handle_signal(signum, frame):
        cancelled["value"] = True

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    ctx = ConversionContext(
        files=sources,
        options=manifest.get("options") or {},
        workdir=Path(manifest["work_dir"]),
        outdir=Path(manifest["output_dir"]),
        settings=settings,
        progress=lambda fraction, message: emit({"type": "progress", "fraction": fraction, "message": message}),
        is_cancelled=lambda: cancelled["value"],
    )
    ctx.workdir.mkdir(parents=True, exist_ok=True)
    ctx.outdir.mkdir(parents=True, exist_ok=True)

    try:
        artifacts = spec.run(ctx)
    except ApiError as exc:
        emit({"type": "error", "code": exc.code, "message": exc.message, "details": exc.details})
        return 1
    except MemoryError:
        emit(
            {
                "type": "error",
                "code": "out_of_memory",
                "message": "The document is too large to process. Try a smaller file or lower resolution.",
            }
        )
        return 1
    except Exception:
        traceback.print_exc()
        emit(
            {
                "type": "error",
                "code": "conversion_failed",
                "message": "The conversion failed because the document could not be processed.",
            }
        )
        return 1

    if cancelled["value"]:
        emit({"type": "error", "code": "cancelled", "message": "The conversion was cancelled."})
        return 1

    # Final integrity gate: never announce a file that is missing or empty.
    payload = []
    total_bytes = 0
    for index, artifact in enumerate(artifacts):
        path = Path(artifact.path).resolve()
        if not path.exists() or not path.is_file() or path.stat().st_size == 0:
            emit(
                {
                    "type": "error",
                    "code": "conversion_failed",
                    "message": "The conversion produced an empty file and was discarded.",
                }
            )
            return 1
        if ctx.outdir.resolve() not in path.parents and path.parent != ctx.outdir.resolve():
            emit(
                {
                    "type": "error",
                    "code": "conversion_failed",
                    "message": "The conversion produced an unexpected output path.",
                }
            )
            return 1
        stored = ctx.outdir / f"artifact-a{index + 1}"
        if path != stored:
            path.replace(stored)
        total_bytes += stored.stat().st_size
        payload.append(
            {
                "path": str(stored),
                "filename": artifact.filename,
                "media_type": artifact.media_type,
                "meta": artifact.meta,
                "is_primary": artifact.is_primary,
            }
        )

    meta = {"outputBytes": total_bytes, "files": len(payload)}
    if artifacts:
        meta["primaryMeta"] = artifacts[0].meta
    emit({"type": "result", "artifacts": payload, "meta": meta, "warnings": []})
    return 0


if __name__ == "__main__":
    sys.exit(main())
