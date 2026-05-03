import json
from pathlib import Path
from cajas.reports.validation_profile_matrix import build_profile_matrix

def test_build_profile_matrix_escalates_ci():
    base_payload = {
        "gates": [
            {
                "name": "required_pass",
                "required": True,
                "status": "pass",
                "reason_code": "ok",
                "action": "none",
                "summary": "ok"
            },
            {
                "name": "optional_warn",
                "required": False,
                "status": "warn",
                "reason_code": "opt_warn",
                "action": "none",
                "summary": "opt warn"
            }
        ],
        "profile": "ci"
    }
    matrix = build_profile_matrix(base_payload=base_payload)
    
    assert "local" in matrix["profiles"]
    assert "ci" in matrix["profiles"]
    assert "strict" in matrix["profiles"]
    
    assert matrix["profiles"]["local"]["overall_status"] == "pass"
    assert matrix["profiles"]["local"]["escalated_count"] == 0
    assert len(matrix["profiles"]["local"]["non_escalated_warnings"]) == 1
    
    assert matrix["profiles"]["ci"]["overall_status"] == "warn"
    assert matrix["profiles"]["ci"]["escalated_count"] == 1
    
    assert matrix["profiles"]["strict"]["overall_status"] == "warn"
    assert matrix["profiles"]["strict"]["escalated_count"] == 1

def test_build_profile_matrix_escalates_strict_missing():
    base_payload = {
        "gates": [
            {
                "name": "optional_missing",
                "required": False,
                "status": "not_run",
                "reason_code": "missing",
                "action": "none",
                "summary": "missing"
            }
        ],
        "profile": "ci"
    }
    matrix = build_profile_matrix(base_payload=base_payload)
    
    assert matrix["profiles"]["local"]["overall_status"] == "pass"
    assert matrix["profiles"]["local"]["escalated_count"] == 0
    
    assert matrix["profiles"]["ci"]["overall_status"] == "pass"
    assert matrix["profiles"]["ci"]["escalated_count"] == 0
    
    assert matrix["profiles"]["strict"]["overall_status"] == "warn"
    assert matrix["profiles"]["strict"]["escalated_count"] == 1

def test_build_profile_matrix_required_fail():
    base_payload = {
        "gates": [
            {
                "name": "required_fail",
                "required": True,
                "status": "fail",
                "reason_code": "bad",
                "action": "fix",
                "summary": "bad"
            }
        ]
    }
    matrix = build_profile_matrix(base_payload=base_payload)
    
    assert matrix["profiles"]["local"]["overall_status"] == "fail"
    assert matrix["profiles"]["ci"]["overall_status"] == "fail"
    assert matrix["profiles"]["strict"]["overall_status"] == "fail"

def test_strict_warning_reason_and_markdown_note():
    from cajas.reports.validation_profile_matrix import render_profile_matrix_markdown

    base_payload = {
        "gates": [
            {
                "name": "optional_missing",
                "required": False,
                "status": "not_run",
                "reason_code": "missing",
                "action": "none",
                "summary": "missing"
            }
        ],
        "profile": "local"
    }
    matrix = build_profile_matrix(base_payload=base_payload)
    assert matrix["profiles"]["strict"]["overall_status"] == "warn"
    assert matrix["profiles"]["strict"]["strict_warning_reason"] is not None
    md = render_profile_matrix_markdown(matrix)
    assert "Strict Warning Note" in md
