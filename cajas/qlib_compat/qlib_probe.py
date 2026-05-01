"""Qlib import and Dataset API compatibility probes."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import importlib
from importlib import metadata


@dataclass(frozen=True)
class QlibImportStatus:
    module: str
    available: bool
    version: str | None
    import_error: str | None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class QlibDatasetApiStatus:
    qlib_available: bool
    dataset_h_available: bool
    data_handler_available: bool
    data_handler_lp_available: bool
    imports: list[QlibImportStatus]
    notes: list[str]

    def to_dict(self) -> dict:
        return {
            "qlib_available": self.qlib_available,
            "dataset_h_available": self.dataset_h_available,
            "data_handler_available": self.data_handler_available,
            "data_handler_lp_available": self.data_handler_lp_available,
            "imports": [x.to_dict() for x in self.imports],
            "notes": list(self.notes),
        }


def _probe_module(module: str) -> QlibImportStatus:
    try:
        importlib.import_module(module)
        version = None
        if module == "qlib":
            try:
                version = metadata.version("pyqlib")
            except metadata.PackageNotFoundError:
                version = None
        return QlibImportStatus(module=module, available=True, version=version, import_error=None)
    except Exception as exc:  # pragma: no cover
        return QlibImportStatus(module=module, available=False, version=None, import_error=f"{type(exc).__name__}: {exc}")


def probe_qlib_dataset_api() -> QlibDatasetApiStatus:
    modules = [
        "qlib",
        "qlib.data.dataset",
        "qlib.data.dataset.handler",
    ]
    statuses = [_probe_module(m) for m in modules]
    by_module = {s.module: s for s in statuses}

    qlib_available = bool(by_module["qlib"].available)
    dataset_h_available = False
    data_handler_available = False
    data_handler_lp_available = False

    if qlib_available and by_module["qlib.data.dataset"].available:
        try:
            dataset_mod = importlib.import_module("qlib.data.dataset")
            dataset_h_available = hasattr(dataset_mod, "DatasetH")
        except Exception:
            dataset_h_available = False

    if qlib_available and by_module["qlib.data.dataset.handler"].available:
        try:
            handler_mod = importlib.import_module("qlib.data.dataset.handler")
            data_handler_available = hasattr(handler_mod, "DataHandler")
            data_handler_lp_available = hasattr(handler_mod, "DataHandlerLP")
        except Exception:
            data_handler_available = False
            data_handler_lp_available = False

    notes: list[str] = []
    if not qlib_available:
        notes.append("Qlib is not importable in the current environment.")
    if qlib_available and not dataset_h_available:
        notes.append("Qlib import works but DatasetH is unavailable.")
    if qlib_available and not data_handler_available:
        notes.append("Qlib import works but DataHandler is unavailable.")
    if qlib_available and not data_handler_lp_available:
        notes.append("Qlib import works but DataHandlerLP is unavailable.")
    notes.append("Probe only; qlib.init() is not called.")

    return QlibDatasetApiStatus(
        qlib_available=qlib_available,
        dataset_h_available=dataset_h_available,
        data_handler_available=data_handler_available,
        data_handler_lp_available=data_handler_lp_available,
        imports=statuses,
        notes=notes,
    )
