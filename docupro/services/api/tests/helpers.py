"""Small helpers shared by the API tests."""

from __future__ import annotations

import time
from pathlib import Path


def wait_for_job(client, job_id: str, timeout: float = 90.0) -> dict:
    deadline = time.time() + timeout
    last = {}
    while time.time() < deadline:
        response = client.get(f"/api/jobs/{job_id}")
        assert response.status_code == 200, response.text
        last = response.json()
        if last["status"] in {"succeeded", "failed", "cancelled", "expired"}:
            return last
        time.sleep(0.2)
    raise AssertionError(f"job {job_id} did not finish in {timeout}s: {last}")


def submit(client, tool: str, paths: list[Path], options: str = "{}", order: str = ""):
    files = []
    handles = []
    try:
        for path in paths:
            handle = path.open("rb")
            handles.append(handle)
            files.append(("files", (path.name, handle, "application/octet-stream")))
        return client.post(
            "/api/jobs",
            data={"tool": tool, "options": options, "order": order},
            files=files,
        )
    finally:
        for handle in handles:
            handle.close()


def download_all(client, job: dict) -> dict[str, bytes]:
    payloads: dict[str, bytes] = {}
    for artifact in job["artifacts"]:
        response = client.get(artifact["url"])
        assert response.status_code == 200, response.text
        payloads[artifact["name"]] = response.content
    return payloads
