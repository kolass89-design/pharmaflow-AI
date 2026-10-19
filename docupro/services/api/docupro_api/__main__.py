"""Allow ``python -m docupro_api`` to start the server."""

import os

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "docupro_api.main:app",
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "8000")),
        workers=1,  # jobs live in-process; scale with replicas, not workers
        proxy_headers=True,
        forwarded_allow_ips="*",
        log_level=os.environ.get("DOCUPRO_LOG_LEVEL", "info").lower(),
    )
