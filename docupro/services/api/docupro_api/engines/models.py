"""Shared data model for conversions: specs, options, sources and artifacts."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

OptionType = Literal["select", "number", "boolean", "text", "password", "pages"]
Category = Literal["pdf", "word", "image", "other"]


@dataclass(frozen=True)
class Choice:
    value: str
    label: str


@dataclass(frozen=True)
class OptionSpec:
    key: str
    label: str
    type: OptionType = "text"
    default: Any = None
    choices: tuple[Choice, ...] = ()
    minimum: float | None = None
    maximum: float | None = None
    step: float | None = None
    help: str | None = None
    required: bool = False
    placeholder: str | None = None
    advanced: bool = False

    def public(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "key": self.key,
            "label": self.label,
            "type": self.type,
            "default": self.default,
        }
        if self.choices:
            data["choices"] = [{"value": c.value, "label": c.label} for c in self.choices]
        for attr in ("minimum", "maximum", "step", "help", "placeholder"):
            value = getattr(self, attr)
            if value is not None:
                data[attr] = value
        if self.required:
            data["required"] = True
        if self.advanced:
            data["advanced"] = True
        return data


@dataclass(frozen=True)
class InputSpec:
    extensions: tuple[str, ...]
    label: str
    media_types: tuple[str, ...] = ()
    max_files: int | None = None
    allows_batch: bool = True

    def public(self) -> dict[str, Any]:
        return {
            "extensions": list(self.extensions),
            "label": self.label,
            "mediaTypes": list(self.media_types),
            "maxFiles": self.max_files,
            "allowsBatch": self.allows_batch,
        }


@dataclass(frozen=True)
class ConversionSpec:
    """Everything needed to describe, validate and run one conversion."""

    id: str
    category: Category
    title: str
    subtitle: str
    description: str
    input: InputSpec
    output_kind: str
    engine: str
    run: Callable[[ConversionContext], list[Artifact]]
    options: tuple[OptionSpec, ...] = ()
    output_label: str = "file"
    output_extension: str = ""
    min_files: int = 1
    max_files: int = 1
    batch: bool = False
    zip_multiple: bool = False
    limitations: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()
    offline_capable: bool = False
    estimated_seconds: int = 5
    featured: bool = False

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category,
            "title": self.title,
            "subtitle": self.subtitle,
            "description": self.description,
            "input": self.input.public(),
            "outputKind": self.output_kind,
            "outputLabel": self.output_label,
            "outputExtension": self.output_extension,
            "engine": self.engine,
            "options": [o.public() for o in self.options],
            "minFiles": self.min_files,
            "maxFiles": self.max_files,
            "batch": self.batch,
            "zipMultiple": self.zip_multiple,
            "limitations": list(self.limitations),
            "keywords": list(self.keywords),
            "offlineCapable": self.offline_capable,
            "estimatedSeconds": self.estimated_seconds,
            "featured": self.featured,
        }


@dataclass
class SourceFile:
    path: Path
    original_name: str
    safe_name: str
    kind: str
    size: int
    pages: int | None = None
    order: int = 0

    @property
    def stem(self) -> str:
        return self.safe_name.rsplit(".", 1)[0] if "." in self.safe_name else self.safe_name


@dataclass
class Artifact:
    path: Path
    filename: str
    media_type: str
    meta: dict[str, Any] = field(default_factory=dict)
    is_primary: bool = True

    @property
    def size(self) -> int:
        try:
            return self.path.stat().st_size
        except OSError:
            return 0

    def public(self, job_id: str | None = None, token: str | None = None) -> dict[str, Any]:
        data: dict[str, Any] = {
            "name": self.filename,
            "mediaType": self.media_type,
            "size": self.size,
            "meta": self.meta,
        }
        if job_id and token:
            digest = hashlib.sha256(self.filename.encode("utf-8")).hexdigest()[:12]
            data["url"] = f"/api/jobs/{job_id}/download/{digest}?token={token}"
        return data


class ConversionContext:
    """Runtime object handed to every engine."""

    def __init__(
        self,
        *,
        files: list[SourceFile],
        options: dict[str, Any],
        workdir: Path,
        outdir: Path,
        settings: Any,
        progress: Callable[[float, str], None],
        is_cancelled: Callable[[], bool],
    ) -> None:
        self.files = files
        self.options = options
        self.workdir = workdir
        self.outdir = outdir
        self.settings = settings
        self._progress = progress
        self._is_cancelled = is_cancelled
        self._artifacts: list[Artifact] = []

    # -- progress / cancellation ------------------------------------------
    def report(self, fraction: float, message: str) -> None:
        self._progress(max(0.0, min(1.0, fraction)), message)

    def check_cancel(self) -> None:
        if self._is_cancelled():
            from ..errors import Cancelled

            raise Cancelled("The conversion was cancelled.")

    # -- options -----------------------------------------------------------
    def opt(self, key: str, default: Any = None) -> Any:
        value = self.options.get(key, default)
        return default if value is None or value == "" else value

    def opt_int(self, key: str, default: int, minimum: int | None = None, maximum: int | None = None) -> int:
        try:
            value = int(self.opt(key, default))
        except (TypeError, ValueError):
            value = default
        if minimum is not None:
            value = max(minimum, value)
        if maximum is not None:
            value = min(maximum, value)
        return value

    def opt_float(self, key: str, default: float, minimum: float | None = None, maximum: float | None = None) -> float:
        try:
            value = float(self.opt(key, default))
        except (TypeError, ValueError):
            value = default
        if minimum is not None:
            value = max(minimum, value)
        if maximum is not None:
            value = min(maximum, value)
        return value

    def opt_bool(self, key: str, default: bool = False) -> bool:
        value = self.options.get(key, default)
        if isinstance(value, bool):
            return value
        if value is None:
            return default
        return str(value).strip().lower() in {"1", "true", "yes", "on"}

    # -- output ------------------------------------------------------------
    def emit(
        self,
        path: Path,
        filename: str,
        media_type: str,
        *,
        meta: dict[str, Any] | None = None,
        is_primary: bool = True,
    ) -> Artifact:
        from ..security import sanitize_filename

        artifact = Artifact(
            path=path,
            filename=sanitize_filename(filename, fallback="document"),
            media_type=media_type,
            meta=meta or {},
            is_primary=is_primary,
        )
        self._artifacts.append(artifact)
        return artifact

    @property
    def artifacts(self) -> list[Artifact]:
        return list(self._artifacts)
