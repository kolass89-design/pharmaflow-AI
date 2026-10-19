"""End-to-end API tests: upload, job lifecycle, downloads and abuse handling."""

from __future__ import annotations

import json
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor

import pymupdf
from helpers import download_all, submit, wait_for_job

from docupro_api.security import RateLimiter


def test_catalog_lists_every_tool(client):
    response = client.get("/api/tools")
    assert response.status_code == 200
    payload = response.json()
    tools = payload["tools"]
    assert len(tools) >= 35
    ids = {tool["id"] for tool in tools}
    for required in ("pdf-to-word", "pdf-to-jpeg", "image-to-pdf", "word-to-pdf", "merge-pdf", "compress-pdf"):
        assert required in ids
    for tool in tools:
        assert tool["title"] and tool["description"]
        assert tool["input"]["extensions"]
        assert isinstance(tool["available"], bool)
        for option in tool["options"]:
            assert option["key"] and option["type"] in {"select", "number", "boolean", "text", "password", "pages"}


def test_health_and_capabilities(client):
    assert client.get("/api/health").json()["status"] == "ok"
    ready = client.get("/api/ready").json()
    assert ready["status"] in {"ready", "degraded"}
    caps = client.get("/api/capabilities").json()
    assert caps["limits"]["maxUploadBytes"] > 0
    assert "ocr" in caps["engines"]


def test_security_headers(client):
    response = client.get("/api/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert "Content-Security-Policy" in response.headers
    assert response.headers["Cache-Control"] == "no-store"


def test_pdf_to_text_job_end_to_end(client, corpus):
    response = submit(client, "pdf-to-text", [corpus / "report-fr.pdf"])
    assert response.status_code == 202, response.text
    job = response.json()
    assert job["status"] in {"queued", "running"}
    assert len(job["id"]) == 32

    final = wait_for_job(client, job["id"])
    assert final["status"] == "succeeded", final
    assert final["progress"] == 1.0
    assert final["artifacts"] and final["artifacts"][0]["size"] > 0
    assert final["expiresAt"] and final["expiresInSeconds"] > 0

    files = download_all(client, final)
    content = next(iter(files.values())).decode("utf-8")
    assert "DOCUPRO" in content
    assert "Rapport annuel" in content
    assert "é" in content  # accents survive


def test_download_requires_token(client, corpus):
    job = submit(client, "pdf-to-text", [corpus / "report-fr.pdf"]).json()
    final = wait_for_job(client, job["id"])
    artifact = final["artifacts"][0]
    bare = f"/api/jobs/{job['id']}/download/{artifact['id']}"
    assert client.get(bare).status_code == 404
    assert client.get(bare + "?token=deadbeef").status_code == 404
    good = client.get(artifact["url"])
    assert good.status_code == 200
    assert "attachment" in good.headers["content-disposition"]
    assert good.headers["cache-control"].startswith("no-store")


def test_job_lookup_requires_unguessable_id(client):
    assert client.get("/api/jobs/" + "0" * 32).status_code == 404
    assert client.get("/api/jobs/not-a-real-id").status_code == 404


def test_unknown_tool_rejected(client, corpus):
    response = submit(client, "not-a-tool", [corpus / "report-fr.pdf"])
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "unknown_tool"


def test_invalid_options_rejected(client, corpus):
    response = submit(client, "pdf-to-jpeg", [corpus / "report-fr.pdf"], options="{bad json")
    assert response.status_code == 400
    response = submit(client, "pdf-to-jpeg", [corpus / "report-fr.pdf"], options=json.dumps({"nope": 1}))
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_option"
    response = submit(client, "protect-pdf", [corpus / "report-fr.pdf"], options="{}")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "missing_option"


def test_wrong_extension_and_spoofed_files(client, corpus):
    response = submit(client, "pdf-to-text", [corpus / "photo.jpg"])
    assert response.status_code == 415
    response = submit(client, "pdf-to-text", [corpus / "fake.pdf"])
    assert response.status_code == 415
    assert response.json()["error"]["code"] == "invalid_file"
    response = submit(client, "pdf-to-text", [corpus / "huge.exe"])
    assert response.status_code == 415


def test_empty_upload_rejected(client, corpus):
    response = submit(client, "pdf-to-text", [corpus / "empty.pdf"])
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_file"


def test_corrupted_pdf_fails_cleanly(client, corpus):
    job = submit(client, "pdf-to-text", [corpus / "corrupted.pdf"]).json()
    final = wait_for_job(client, job["id"])
    assert final["status"] == "failed"
    assert final["error"]["code"] in {"conversion_failed", "invalid_file"}
    assert "Traceback" not in json.dumps(final)
    assert "/tmp" not in json.dumps(final)


def test_password_protected_pdf_requires_unlock(client, corpus):
    job = submit(client, "pdf-to-text", [corpus / "protected.pdf"]).json()
    final = wait_for_job(client, job["id"])
    assert final["status"] == "failed"
    assert final["error"]["code"] == "password_required"

    wrong = submit(client, "unlock-pdf", [corpus / "protected.pdf"], options=json.dumps({"password": "bad"})).json()
    wrong_final = wait_for_job(client, wrong["id"])
    assert wrong_final["status"] == "failed"
    assert wrong_final["error"]["code"] == "invalid_password"

    right = submit(
        client, "unlock-pdf", [corpus / "protected.pdf"], options=json.dumps({"password": "motdepasse"})
    ).json()
    right_final = wait_for_job(client, right["id"])
    assert right_final["status"] == "succeeded", right_final
    payload = download_all(client, right_final)
    data = next(iter(payload.values()))
    with pymupdf.open(stream=data, filetype="pdf") as doc:
        assert not doc.needs_pass


def test_merge_multiple_files_and_zip_downloads(client, corpus):
    job = submit(client, "merge-pdf", [corpus / "report-fr.pdf", corpus / "scan-fr.pdf"]).json()
    final = wait_for_job(client, job["id"])
    assert final["status"] == "succeeded", final
    payload = download_all(client, final)
    data = next(iter(payload.values()))
    with pymupdf.open(stream=data, filetype="pdf") as doc:
        assert doc.page_count == 4
    assert len(final["inputs"]) == 2

    zip_job = submit(client, "pdf-to-png", [corpus / "report-fr.pdf"], options=json.dumps({"dpi": 80})).json()
    zip_final = wait_for_job(client, zip_job["id"])
    payload = download_all(client, zip_final)
    archive = next(iter(payload.values()))
    with zipfile.ZipFile(__import__("io").BytesIO(archive)) as zf:
        assert len(zf.namelist()) == 3


def test_multiple_uploads_and_order(client, corpus):
    job = submit(
        client,
        "image-to-pdf",
        [corpus / "photo.jpg", corpus / "logo-alpha.png"],
        options=json.dumps({"page_size": "fit"}),
        order="2,1",
    ).json()
    final = wait_for_job(client, job["id"])
    assert final["status"] == "succeeded", final
    assert final["meta"]["primaryMeta"]["pages"] == 2

    bad_order = submit(client, "image-to-pdf", [corpus / "photo.jpg"], order="2")
    assert bad_order.status_code == 400


def test_too_many_files_rejected(client, corpus):
    response = submit(client, "pdf-to-text", [corpus / "report-fr.pdf"] * 2)
    assert response.status_code == 400
    assert response.json()["error"]["code"] in {"too_many_files"}


def test_cancel_job(client, corpus):
    job = submit(client, "pdf-to-searchable", [corpus / "scan-fr.pdf"]).json()
    time.sleep(0.2)
    cancelled = client.post(f"/api/jobs/{job['id']}/cancel")
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] in {"cancelled", "succeeded"}
    final = wait_for_job(client, job["id"])
    assert final["status"] in {"cancelled", "succeeded"}


def test_delete_job_removes_files(client, corpus):
    job = submit(client, "pdf-to-text", [corpus / "report-fr.pdf"]).json()
    final = wait_for_job(client, job["id"])
    assert final["status"] == "succeeded"
    url = final["artifacts"][0]["url"]
    assert client.delete(f"/api/jobs/{job['id']}").status_code == 204
    assert client.get(f"/api/jobs/{job['id']}").status_code == 200
    assert client.get(url).status_code == 404


def test_expired_job_files_are_deleted(client, corpus):
    job = submit(client, "pdf-to-text", [corpus / "report-fr.pdf"]).json()
    final = wait_for_job(client, job["id"])
    assert final["status"] == "succeeded"
    manager = client.app.state.manager
    managed = manager.get(job["id"])
    with managed.lock:
        managed.expires_at = time.time() - 1
    manager.sweep()
    assert client.get(final["artifacts"][0]["url"]).status_code == 404
    assert not managed.output_dir.exists()


def test_rate_limit_enforced(client):
    original = client.app.state.limiter
    client.app.state.limiter = RateLimiter(1, 1)
    try:
        first = client.get("/api/jobs/" + "0" * 32)
        assert first.status_code == 404
        response = client.get("/api/jobs/" + "0" * 32)
        assert response.status_code == 429
        assert "Retry-After" in response.headers
    finally:
        client.app.state.limiter = original


def test_path_traversal_filename_is_neutralised(client, corpus):
    payload = (corpus / "report-fr.pdf").read_bytes()
    response = client.post(
        "/api/jobs",
        data={"tool": "pdf-to-text", "options": "{}"},
        files=[("files", ("../../etc/passwd.pdf", payload, "application/pdf"))],
    )
    assert response.status_code == 202, response.text
    final = wait_for_job(client, response.json()["id"])
    assert final["status"] == "succeeded"
    assert ".." not in final["artifacts"][0]["name"]
    assert "/" not in final["artifacts"][0]["name"]


def test_concurrent_jobs(client, corpus):
    def one(index: int) -> str:
        response = submit(client, "pdf-to-text", [corpus / "report-fr.pdf"])
        assert response.status_code == 202, response.text
        return response.json()["id"]

    with ThreadPoolExecutor(max_workers=4) as pool:
        ids = list(pool.map(one, range(4)))
    for job_id in ids:
        final = wait_for_job(client, job_id, timeout=120)
        assert final["status"] == "succeeded", final


def test_no_web_build_serves_api_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["name"].startswith("DOCUPRO")


def test_unavailable_tool_reports_reason(client):
    tools = {tool["id"]: tool for tool in client.get("/api/tools").json()["tools"]}
    unavailable = [t for t in tools.values() if not t["available"]]
    for tool in unavailable:
        assert tool["unavailableReason"]


def test_download_rejects_unknown_artifact_id(client, corpus):
    """A valid token must not unlock a different artifact slot."""
    job = submit(client, "pdf-to-text", [corpus / "report-fr.pdf"]).json()
    final = wait_for_job(client, job["id"])
    token = final["artifacts"][0]["url"].split("token=")[1]
    response = client.get(f"/api/jobs/{job['id']}/download/a7?token={token}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "artifact_not_found"


def test_download_shortens_retention():
    """After the last artifact is downloaded, expiry is brought forward."""
    import time
    from dataclasses import replace
    from pathlib import Path
    from types import SimpleNamespace

    from docupro_api.config import get_settings
    from docupro_api.jobs import Job, JobManager

    settings = replace(get_settings(), delete_after_download_seconds=60)
    now = time.time()
    job = Job(
        id="a" * 32,
        tool="pdf-to-text",
        token="t" * 32,
        status="succeeded",
        options={},
        inputs=[],
        created_at=now,
        expires_at=now + 1800,
        root=Path("/tmp/docupro-retention"),
        max_seconds=60,
    )
    job.artifacts = [{"id": "a1"}, {"id": "a2"}]

    manager = SimpleNamespace(settings=settings)
    JobManager.register_download(manager, job, "a1")
    assert job.expires_at == now + 1800, "a single download must not shorten retention"

    JobManager.register_download(manager, job, "a2")
    assert job.expires_at <= time.time() + 61
    assert job.expires_at > time.time() + 50


def test_settings_accept_configured_delete_window(monkeypatch):
    from docupro_api.config import Settings

    monkeypatch.setenv("DOCUPRO_DELETE_AFTER_DOWNLOAD_SECONDS", "45")
    assert Settings().delete_after_download_seconds == 45


def test_artifact_layout_uses_opaque_names(client, corpus):
    """Stored files never carry user-controlled names."""
    job = submit(client, "pdf-to-text", [corpus / "report-fr.pdf"]).json()
    wait_for_job(client, job["id"])
    manager = __import__("docupro_api.main", fromlist=["app"]).app.state.manager
    stored = sorted(p.name for p in (manager.get(job["id"]).output_dir).iterdir())
    assert stored == ["artifact-a1"]
    assert manager.get(job["id"]).inputs[0]["name"] == "report-fr.pdf"


def test_delete_removes_the_whole_job_directory(client, corpus):
    """Deleting a job must not leave an empty directory behind on disk."""
    job = submit(client, "pdf-to-text", [corpus / "report-fr.pdf"]).json()
    wait_for_job(client, job["id"])
    manager = __import__("docupro_api.main", fromlist=["app"]).app.state.manager
    root = manager.get(job["id"]).root
    assert root.exists()
    assert client.delete(f"/api/jobs/{job['id']}").status_code == 204
    assert not root.exists(), "job directory should be removed entirely"


def test_expiry_removes_the_whole_job_directory(client, corpus):
    import time

    job = submit(client, "pdf-to-text", [corpus / "report-fr.pdf"]).json()
    wait_for_job(client, job["id"])
    manager = client.app.state.manager
    managed = manager.get(job["id"])
    root = managed.root
    with managed.lock:
        managed.expires_at = time.time() - 1
    manager.sweep()
    assert not root.exists(), "expired job directory should be removed entirely"
