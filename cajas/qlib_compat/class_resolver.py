"""Class path resolution utilities for non-executing dry-run validation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import importlib


@dataclass(frozen=True)
class ClassResolutionResult:
    dotted_path: str
    module_path: str
    attribute_name: str
    resolved: bool
    object_type: str | None
    import_error: str | None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ClassResolverReport:
    results: list[ClassResolutionResult]

    @property
    def unresolved(self) -> list[ClassResolutionResult]:
        return [item for item in self.results if not item.resolved]

    def to_dict(self) -> dict:
        return {
            "results": [item.to_dict() for item in self.results],
            "unresolved": [item.to_dict() for item in self.unresolved],
        }


def resolve_dotted_path(dotted_path: str) -> ClassResolutionResult:
    path = str(dotted_path).strip()
    if not path:
        return ClassResolutionResult(
            dotted_path=path,
            module_path="",
            attribute_name="",
            resolved=False,
            object_type=None,
            import_error="empty dotted path",
        )

    module_path, separator, attribute_name = path.rpartition(".")
    if not separator or not module_path or not attribute_name:
        return ClassResolutionResult(
            dotted_path=path,
            module_path=module_path,
            attribute_name=attribute_name,
            resolved=False,
            object_type=None,
            import_error="dotted path must include module and attribute",
        )

    try:
        module = importlib.import_module(module_path)
    except (ImportError, ModuleNotFoundError) as exc:
        return ClassResolutionResult(
            dotted_path=path,
            module_path=module_path,
            attribute_name=attribute_name,
            resolved=False,
            object_type=None,
            import_error=f"{type(exc).__name__}: {exc}",
        )

    try:
        resolved_obj = getattr(module, attribute_name)
    except AttributeError as exc:
        return ClassResolutionResult(
            dotted_path=path,
            module_path=module_path,
            attribute_name=attribute_name,
            resolved=False,
            object_type=None,
            import_error=f"AttributeError: {exc}",
        )

    return ClassResolutionResult(
        dotted_path=path,
        module_path=module_path,
        attribute_name=attribute_name,
        resolved=True,
        object_type=type(resolved_obj).__name__,
        import_error=None,
    )


def resolve_dotted_paths(paths: list[str] | tuple[str, ...]) -> ClassResolverReport:
    return ClassResolverReport(results=[resolve_dotted_path(path) for path in paths])
