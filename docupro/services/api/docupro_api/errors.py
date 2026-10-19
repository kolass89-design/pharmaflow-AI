"""Structured API errors.

Every failure the client can trigger is expressed as an ``ApiError`` with a
stable machine readable code, a user facing message and an HTTP status.
Internal details (paths, stack traces) never reach the client.
"""

from __future__ import annotations

from typing import Any


class ApiError(Exception):
    status_code: int = 400
    code: str = "bad_request"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.details:
            payload["details"] = self.details
        return {"error": payload}


class ValidationError(ApiError):
    status_code = 400
    code = "invalid_request"


class UnsupportedInput(ApiError):
    status_code = 415
    code = "unsupported_input"


class PayloadTooLarge(ApiError):
    status_code = 413
    code = "file_too_large"


class NotFound(ApiError):
    status_code = 404
    code = "not_found"


class RateLimited(ApiError):
    status_code = 429
    code = "rate_limited"


class EngineUnavailable(ApiError):
    status_code = 503
    code = "engine_unavailable"


class ConversionFailed(ApiError):
    status_code = 422
    code = "conversion_failed"


class QueueFull(ApiError):
    status_code = 503
    code = "queue_full"


class JobTimeout(ApiError):
    status_code = 504
    code = "conversion_timeout"


class Cancelled(ApiError):
    status_code = 409
    code = "cancelled"
