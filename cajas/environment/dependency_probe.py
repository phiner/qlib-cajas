"""Probe optional dependencies for future baseline phases."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import importlib


@dataclass(frozen=True)
class DependencyStatus:
    name: str
    available: bool
    version: str | None
    import_error: str | None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class DependencyProbeReport:
    dependencies: list[DependencyStatus]

    def to_dict(self) -> dict:
        return {"dependencies": [d.to_dict() for d in self.dependencies]}

    @property
    def missing(self) -> list[str]:
        return [d.name for d in self.dependencies if not d.available]


def probe_dependencies(
    names: tuple[str, ...] = ("pandas", "yaml", "sklearn", "lightgbm"),
) -> DependencyProbeReport:
    deps: list[DependencyStatus] = []
    for name in names:
        try:
            module = importlib.import_module(name)
            version = getattr(module, "__version__", None)
            deps.append(
                DependencyStatus(
                    name=name,
                    available=True,
                    version=str(version) if version is not None else None,
                    import_error=None,
                )
            )
        except Exception as exc:
            deps.append(
                DependencyStatus(
                    name=name,
                    available=False,
                    version=None,
                    import_error=str(exc),
                )
            )
    return DependencyProbeReport(dependencies=deps)
