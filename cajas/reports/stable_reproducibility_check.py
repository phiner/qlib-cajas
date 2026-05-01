"""Compare stable fingerprint reports."""

from __future__ import annotations


def _index(rep: dict) -> dict[str, str]:
    return {item["relative_path"]: item["stable_hash"] for item in rep.get("included_files", [])}


def build_stable_reproducibility_report(*, left: dict, right: dict) -> dict:
    li = _index(left)
    ri = _index(right)
    lk = set(li)
    rk = set(ri)
    shared = sorted(lk & rk)
    missing_left = sorted(lk - rk)
    missing_right = sorted(rk - lk)
    mismatches = []
    matches = []
    for k in shared:
        if li[k] == ri[k]:
            matches.append(k)
        else:
            mismatches.append({"relative_path": k, "left": li[k], "right": ri[k]})

    warnings = []
    if missing_left or missing_right:
        warnings.append("artifact set differs")

    if mismatches:
        status = "not_stable_reproducible"
    elif warnings:
        status = "stable_reproducible_with_warnings"
    else:
        status = "stable_reproducible"

    return {
        "schema_version": "v1",
        "left_root": left.get("root"),
        "right_root": right.get("root"),
        "matching_normalized_artifacts": matches,
        "missing_left": missing_left,
        "missing_right": missing_right,
        "changed_normalized_hashes": mismatches,
        "skipped_files_left": left.get("skipped_files", []),
        "skipped_files_right": right.get("skipped_files", []),
        "expected_variability_absorbed_count": len(matches),
        "true_mismatch_count": len(mismatches),
        "warnings": warnings,
        "final_status": status,
    }
