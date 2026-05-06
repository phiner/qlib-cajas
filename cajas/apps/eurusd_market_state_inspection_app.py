"""Chart-first EURUSD four-layer market-state inspection app."""

from __future__ import annotations

from pathlib import Path

from cajas.research.eurusd_market_state_inspection_gui import (
    AGREEMENT_VALUES,
    build_inspection_chart,
    build_layer_summary,
    compute_chart_window,
    compute_layer_highlights,
    default_feedback_values,
    build_compressed_time_axis,
    load_completed_feedback,
    load_inspection_packet,
    load_raw_clean_csv,
    merge_packet_with_completed,
    persist_feedback,
)

DEFAULT_PACKET_CSV = Path("tmp/eurusd/EURUSD_15m_market_state_inspection_packet.csv")
DEFAULT_RAW_CSV = Path("tmp/eurusd/EURUSD_15m_Bid_clean_view.csv")
DEFAULT_COMPLETED_CSV = Path("tmp/eurusd/EURUSD_15m_market_state_inspection_packet_completed.csv")
DEFAULT_AUDIT_JSONL = Path("tmp/eurusd/EURUSD_15m_market_state_inspection_feedback_events.jsonl")


def main() -> None:
    try:
        import streamlit as st
    except ImportError as exc:
        raise RuntimeError(
            "Streamlit is not available. Install with: ./.venv-qlib313/bin/python -m pip install streamlit plotly"
        ) from exc

    st.set_page_config(page_title="EURUSD Market-state Inspection", layout="wide")
    st.title("EURUSD 四层市场状态图表审阅")

    packet_csv = DEFAULT_PACKET_CSV
    raw_csv = DEFAULT_RAW_CSV
    completed_csv = DEFAULT_COMPLETED_CSV
    audit_jsonl = DEFAULT_AUDIT_JSONL
    total_bars = 176

    try:
        packet = load_inspection_packet(packet_csv)
        raw_df = load_raw_clean_csv(raw_csv)
        completed = load_completed_feedback(completed_csv)
        merged = merge_packet_with_completed(packet, completed)
    except Exception as exc:
        st.error(f"Failed to load inspection context: {exc}")
        return

    if merged.empty:
        st.warning("Inspection packet is empty.")
        return

    total = len(merged)
    if "market_state_index" not in st.session_state:
        st.session_state.market_state_index = 0
    if "market_state_jump_input" not in st.session_state:
        st.session_state.market_state_jump_input = ""
    idx = max(0, min(int(st.session_state.market_state_index), total - 1))
    row = merged.iloc[idx]

    controls = st.columns([1.1, 1.2, 1, 1, 1, 1, 1.8])
    controls[0].markdown(f"**Sample {idx + 1}/{total}**")
    controls[1].markdown(f"`confidence={row.get('structure_confidence', '')}`")
    if controls[2].button("Previous", use_container_width=True):
        st.session_state.market_state_index = max(0, idx - 1)
        st.rerun()
    if controls[3].button("Next", use_container_width=True):
        st.session_state.market_state_index = min(total - 1, idx + 1)
        st.rerun()
    jump_sample = controls[4].text_input("Jump sample_id", key="market_state_jump_input", label_visibility="collapsed", placeholder="sample_id")
    if controls[5].button("Jump", use_container_width=True) and jump_sample:
        matched = merged.index[merged["sample_id"].astype(str) == jump_sample].tolist()
        if matched:
            st.session_state.market_state_index = int(matched[0])
            st.rerun()
        st.warning(f"sample_id not found: {jump_sample}")

    try:
        window_df, target_local_idx = compute_chart_window(raw_df, str(row["timestamp"]), total_bars=total_bars)
        highlights = compute_layer_highlights(target_local_idx, row)
        fig = build_inspection_chart(window_df, target_local_idx, highlights)
    except Exception as exc:
        st.error(f"Chart build failed: {exc}")
        return

    st.plotly_chart(fig, width="stretch", height=560)

    st.caption(
        f"Rows={total} | current={idx + 1} | p3={row.get('pattern_3_actual_bars_used', '')} "
        f"m8={row.get('market_8_actual_bars_used', '')} m24={row.get('market_24_actual_bars_used', '')} "
        f"m128={row.get('market_128_actual_bars_used', '')} | confidence={row.get('structure_confidence', '')} | "
        "research-only, no LLM, no trading"
    )

    st.subheader("Layer Summary")
    st.dataframe(build_layer_summary(row), hide_index=True, width="stretch")

    rat1, rat2 = st.columns(2)
    with rat1:
        st.caption(f"pattern_3: {row.get('pattern_3_rationale_zh', '')}")
        st.caption(f"market_8: {row.get('market_8_rationale_zh', '')}")
        st.caption(f"market_24: {row.get('market_24_rationale_zh', '')}")
    with rat2:
        st.caption(f"market_128: {row.get('market_128_rationale_zh', '')}")
        st.caption(f"combined: {row.get('market_state_rationale_zh', '')}")

    st.subheader("Manual Feedback")
    defaults = default_feedback_values(row)
    agree_opts = sorted(AGREEMENT_VALUES, key=lambda x: (x != "", x))
    def _layer_fields(name: str, agree_key: str, correct_key: str, fb_key: str) -> tuple[str, str, str]:
        c1, c2, c3 = st.columns([1, 1.3, 2.2])
        with c1:
            agree = st.selectbox(agree_key, agree_opts, index=agree_opts.index(defaults[agree_key]) if defaults[agree_key] in agree_opts else 0, key=f"{name}_agree")
        with c2:
            correct = st.text_input(correct_key, value=defaults[correct_key], key=f"{name}_correct")
        with c3:
            fb = st.text_area(fb_key, value=defaults[fb_key], height=70, key=f"{name}_fb")
        return agree, correct, fb

    hp3_agree, hp3_correct, hp3_fb = _layer_fields("p3", "human_pattern_3_agreement", "human_pattern_3_correct_label", "human_pattern_3_feedback_zh")
    hm8_agree, hm8_correct, hm8_fb = _layer_fields("m8", "human_market_8_agreement", "human_market_8_correct_state", "human_market_8_feedback_zh")
    hm24_agree, hm24_correct, hm24_fb = _layer_fields("m24", "human_market_24_agreement", "human_market_24_correct_state", "human_market_24_feedback_zh")
    hm128_agree, hm128_correct, hm128_fb = _layer_fields("m128", "human_market_128_agreement", "human_market_128_correct_state", "human_market_128_feedback_zh")
    hlocal_agree, hlocal_correct, hlocal_fb = _layer_fields("local", "human_local_structure_agreement", "human_local_structure_correct_state", "human_local_structure_feedback_zh")

    di1, di2 = st.columns(2)
    with di1:
        hdef = st.text_area("human_definition_issue_zh", value=defaults["human_definition_issue_zh"], height=80)
    with di2:
        hrule = st.text_area("human_rule_adjustment_suggestion_zh", value=defaults["human_rule_adjustment_suggestion_zh"], height=80)

    payload = {
        **row.to_dict(),
        "human_pattern_3_agreement": hp3_agree,
        "human_pattern_3_correct_label": hp3_correct,
        "human_pattern_3_feedback_zh": hp3_fb,
        "human_market_8_agreement": hm8_agree,
        "human_market_8_correct_state": hm8_correct,
        "human_market_8_feedback_zh": hm8_fb,
        "human_market_24_agreement": hm24_agree,
        "human_market_24_correct_state": hm24_correct,
        "human_market_24_feedback_zh": hm24_fb,
        "human_market_128_agreement": hm128_agree,
        "human_market_128_correct_state": hm128_correct,
        "human_market_128_feedback_zh": hm128_fb,
        "human_local_structure_agreement": hlocal_agree,
        "human_local_structure_correct_state": hlocal_correct,
        "human_local_structure_feedback_zh": hlocal_fb,
        "human_definition_issue_zh": hdef,
        "human_rule_adjustment_suggestion_zh": hrule,
    }

    c_save, c_save_next = st.columns(2)
    if c_save.button("Save", use_container_width=True):
        result = persist_feedback(payload, completed_csv=completed_csv, audit_jsonl=audit_jsonl)
        if result.get("status") == "ok":
            st.success(f"Saved sample_id={result['sample_id']}")
        else:
            st.error(f"Save blocked: {result.get('errors', [])}")
    if c_save_next.button("Save and Next", use_container_width=True):
        result = persist_feedback(payload, completed_csv=completed_csv, audit_jsonl=audit_jsonl)
        if result.get("status") == "ok":
            st.session_state.market_state_index = min(total - 1, idx + 1)
            st.rerun()
        else:
            st.error(f"Save blocked: {result.get('errors', [])}")

    with st.expander("Advanced / Debug", expanded=False):
        axis_info = build_compressed_time_axis(window_df)
        st.json(
            {
                "paths": {
                    "inspection_packet_csv": str(packet_csv),
                    "raw_clean_csv": str(raw_csv),
                    "completed_feedback_csv": str(completed_csv),
                    "audit_jsonl": str(audit_jsonl),
                },
                "sample_id": row.get("sample_id", ""),
                "timestamp": row.get("timestamp", ""),
                "gap_count": len(axis_info.get("gap_markers", [])),
                "largest_gap_hours": max([float(g.get("gap_hours", 0.0)) for g in axis_info.get("gap_markers", [])], default=0.0),
                "target_local_idx": target_local_idx,
                "highlights": highlights,
                "raw_time_axis_preserved_in_hover": axis_info.get("raw_time_axis_preserved_in_hover", True),
            }
        )


if __name__ == "__main__":
    main()
