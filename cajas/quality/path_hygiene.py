"""Path hygiene checks to catch recurring typo paths in repo text."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import fnmatch


SKIP_DIR_NAMES = {".git", "__pycache__", ".codex"}


@dataclass(frozen=True)
class PathHygieneIssue:
    path: str
    line: int
    pattern: str
    message: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class PathHygieneReport:
    checked_files: int
    issues: list[PathHygieneIssue]

    @property
    def passed(self) -> bool:
        return len(self.issues) == 0

    def to_dict(self) -> dict:
        return {
            "checked_files": self.checked_files,
            "issues": [i.to_dict() for i in self.issues],
            "passed": self.passed,
        }


def _should_skip_path(path: Path) -> bool:
    parts = set(path.parts)
    if "tmp" in parts:
        return True
    if any(p.startswith(".venv") for p in parts):
        return True
    if "tests" in parts:
        return True
    return any(p in SKIP_DIR_NAMES for p in parts)


def _is_command_like_md_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    starters = (
        "./",
        "python",
        "pytest",
        "find ",
        "rm ",
        "git ",
        "cajas/",
    )
    return stripped.startswith(starters)


def check_path_hygiene(
    *,
    root: str | Path,
    include_globs: tuple[str, ...] = (
        "tasks/*.md",
        "cajas/**/*.md",
        "cajas/**/*.py",
        "cajas/**/*.yaml",
        "cajas/**/*.yml",
    ),
    forbidden_patterns: tuple[str, ...] = ("caixas/", "taskDocs/"),
) -> PathHygieneReport:
    root_path = Path(root).resolve()
    issues: list[PathHygieneIssue] = []
    matched_files: set[Path] = set()

    for rel in [p.relative_to(root_path) for p in root_path.rglob("*") if p.is_file()]:
        rel_str = rel.as_posix()
        if _should_skip_path(rel):
            continue
        if not any(fnmatch.fnmatch(rel_str, pat) for pat in include_globs):
            continue
        file_path = root_path / rel
        matched_files.add(file_path)

        # Enforce package initializer naming policy under cajas/.
        if rel_str.startswith("cajas/") and rel.name == "init.py":
            issues.append(
                PathHygieneIssue(
                    path=rel_str,
                    line=1,
                    pattern="cajas/**/init.py",
                    message="Python package initializer must be named __init__.py, not init.py.",
                )
            )

        ext = file_path.suffix.lower()
        with file_path.open("r", encoding="utf-8", errors="ignore") as f:
            for idx, line in enumerate(f, start=1):
                for pat in forbidden_patterns:
                    if pat not in line:
                        continue
                    stripped = line.strip()
                    if stripped in {pat, f"- {pat}", f'"{pat}"', f"'{pat}'"}:
                        continue
                    if "forbidden_patterns" in stripped:
                        continue
                    if stripped.startswith("patterns ="):
                        continue
                    if ext == ".md" and not _is_command_like_md_line(line):
                        continue
                    issues.append(
                        PathHygieneIssue(
                            path=rel_str,
                            line=idx,
                            pattern=pat,
                            message=f"Forbidden path pattern found: {pat}",
                        )
                    )

    return PathHygieneReport(checked_files=len(matched_files), issues=issues)
