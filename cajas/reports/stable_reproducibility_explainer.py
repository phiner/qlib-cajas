"""Explain stable reproducibility outcomes in actionable categories."""

from __future__ import annotations

def _index(fp: dict) -> dict[str, str]:
    return {item["relative_path"]: item["stable_hash"] for item in fp.get("included_files", [])}


def build_stable_reproducibility_explanation(
    *,
    left_fingerprint: dict,
    right_fingerprint: dict,
    stable_repro_report: dict,
    left_manifest: dict | None = None,
    right_manifest: dict | None = None,
) -> dict:
    li = _index(left_fingerprint)
    ri = _index(right_fingerprint)
    shared = sorted(set(li) & set(ri))

    matching = sorted(stable_repro_report.get("matching_normalized_artifacts", []))
    mismatch_items = stable_repro_report.get("changed_normalized_hashes", [])
    missing_left = sorted(stable_repro_report.get("missing_left", []))
    missing_right = sorted(stable_repro_report.get("missing_right", []))

    classification = "unknown"
    recommended = "Inspect stable fingerprints and manifests."
    should_block = True

    if missing_left or missing_right:
        classification = "missing_artifact"
        recommended = "Ensure both runs emit the same artifact set before readiness promotion."
    elif mismatch_items:
        mismatch_paths = [m.get("relative_path", "") for m in mismatch_items]
        variable_only = all(any(tok in p.lower() for tok in ("manifest", "catalog", "lineage", "review", "bundle", "reproducibility_report")) for p in mismatch_paths if p)
        if variable_only:
            classification = "normalization_gap"
            recommended = "Add conservative normalization rules for non-semantic variable fields only."
            should_block = False
        else:
            classification = "semantic_mismatch"
            recommended = "Treat as potential semantic drift; keep readiness blocked until reviewed."
    elif stable_repro_report.get("final_status") == "stable_reproducible_with_warnings":
        classification = "expected_variability_not_normalized"
        recommended = "Review warnings and decide if conservative normalization can absorb expected variability."
        should_block = False
    elif stable_repro_report.get("final_status") == "stable_reproducible":
        classification = "unknown"
        recommended = "No action required for stable reproducibility."
        should_block = False

    fields = []
    for m in mismatch_items:
        rp = m.get("relative_path", "")
        if rp.endswith(".json"):
            fields.append({"relative_path": rp, "likely_fields": ["root", "absolute_path", "working_directory", "created_at_utc"]})
        else:
            fields.append({"relative_path": rp, "likely_fields": ["timestamp-like text", "temp paths", "run labels"]})

    return {
        "schema_version": "v1",
        "top_level_status": stable_repro_report.get("final_status"),
        "classification": classification,
        "should_final_readiness_remain_blocked": should_block,
        "mismatch_categories": {
            "missing_artifact_count": len(missing_left) + len(missing_right),
            "hash_mismatch_count": len(mismatch_items),
            "shared_artifact_count": len(shared),
        },
        "matching_after_normalization": matching,
        "mismatching_after_normalization": mismatch_items,
        "likely_responsible_fields": fields,
        "recommended_remediation": recommended,
        "remaining_blockers": [
            {
                "relative_path": m.get("relative_path"),
                "reason": "non-semantic drift suspected" if classification == "normalization_gap" else "semantic drift suspected",
            }
            for m in mismatch_items
        ],
        "manifest_context": {
            "left_root": (left_manifest or {}).get("root"),
            "right_root": (right_manifest or {}).get("root"),
        },
    }


def render_stable_reproducibility_explanation_md(*, explanation: dict) -> str:
    lines = [
        "# Stable Reproducibility Explanation",
        "",
        f"- top_level_status: `{explanation.get('top_level_status')}`",
        f"- classification: `{explanation.get('classification')}`",
        f"- should_final_readiness_remain_blocked: `{explanation.get('should_final_readiness_remain_blocked')}`",
        "",
        "## Mismatch Categories",
    ]
    cats = explanation.get("mismatch_categories", {})
    lines.append(f"- missing_artifact_count: `{cats.get('missing_artifact_count')}`")
    lines.append(f"- hash_mismatch_count: `{cats.get('hash_mismatch_count')}`")
    lines.append(f"- shared_artifact_count: `{cats.get('shared_artifact_count')}`")
    lines += ["", "## Recommended Remediation", f"- {explanation.get('recommended_remediation')}"]

    lines += ["", "## Mismatching Artifacts"]
    mismatches = explanation.get("mismatching_after_normalization", [])
    if not mismatches:
        lines.append("- none")
    else:
        for item in mismatches:
            lines.append(f"- `{item.get('relative_path')}`")
    return "\n".join(lines) + "\n"
