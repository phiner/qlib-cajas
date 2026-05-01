"""Reproducibility checks across two pipeline manifests."""

from __future__ import annotations


IGNORED_KEYS = {"created_at_utc", "absolute_path", "working_directory"}


def _index_inventory(manifest: dict) -> dict[str, dict]:
    out = {}
    for item in manifest.get("artifact_inventory", []):
        out[item.get("relative_path", "")] = item
    return out


def build_reproducibility_report(*, left_manifest: dict, right_manifest: dict) -> dict:
    left_inv = _index_inventory(left_manifest)
    right_inv = _index_inventory(right_manifest)

    left_keys = set(left_inv)
    right_keys = set(right_inv)
    shared = sorted(left_keys & right_keys)
    left_only = sorted(left_keys - right_keys)
    right_only = sorted(right_keys - left_keys)

    checksum_mismatch: list[dict] = []
    matching: list[str] = []

    for k in shared:
        l = left_inv[k]
        r = right_inv[k]
        if l.get("sha256") and r.get("sha256") and l.get("sha256") != r.get("sha256"):
            checksum_mismatch.append({"relative_path": k, "left": l.get("sha256"), "right": r.get("sha256")})
        else:
            matching.append(k)

    warnings: list[str] = []
    if left_only or right_only:
        warnings.append("artifact presence differs between manifests")

    if checksum_mismatch:
        status = "not_reproducible"
    elif warnings:
        status = "reproducible_with_warnings"
    else:
        status = "reproducible"

    return {
        "schema_version": "v1",
        "left_root": left_manifest.get("root"),
        "right_root": right_manifest.get("root"),
        "matching_artifacts": matching,
        "missing_left": left_only,
        "missing_right": right_only,
        "checksum_mismatches": checksum_mismatch,
        "intentionally_variable_fields": sorted(IGNORED_KEYS),
        "warnings": warnings,
        "final_status": status,
    }
