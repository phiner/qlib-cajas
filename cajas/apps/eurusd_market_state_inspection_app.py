"""Chart-first EURUSD four-layer market-state inspection app."""

from __future__ import annotations

from pathlib import Path

from cajas.research.eurusd_market_state_inspection_gui import (
    AGREEMENT_VALUES,
    build_inspection_chart,
    compute_chart_window,
    compute_layer_highlights,
    default_feedback_values,
    load_completed_feedback,
    load_inspection_packet,
    load_raw_clean_csv,
    merge_packet_with_completed,
    persist_feedback,
)


def main() -> None:
    try:
        import streamlit as st
    except ImportError as exc:
        raise RuntimeError(
            "Streamlit is not available. Install with: ./.venv-qlib313/bin/python -m pip install streamlit plotly"
        ) from exc

    st.set_page_config(page_title="EURUSD Market-state Inspection", layout="wide")
    st.title("EURUSD 四层市场状态图表审阅")

    st.sidebar.header("Paths")
    packet_csv = Path(st.sidebar.text_input("Inspection Packet CSV", "tmp/eurusd/EURUSD_15m_market_state_inspection_packet.csv"))
    raw_csv = Path(st.sidebar.text_input("Raw Clean CSV", "tmp/eurusd/EURUSD_15m_Bid_clean_view.csv"))
    completed_csv = Path(st.sidebar.text_input("Completed Feedback CSV", "tmp/eurusd/EURUSD_15m_market_state_inspection_packet_completed.csv"))
    audit_jsonl = Path(st.sidebar.text_input("Audit JSONL", "tmp/eurusd/EURUSD_15m_market_state_inspection_feedback_events.jsonl"))
    total_bars = int(st.sidebar.number_input("Chart Bars", min_value=144, max_value=300, value=176, step=8))

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
    idx = max(0, min(int(st.session_state.market_state_index), total - 1))
    jump_sample = st.sidebar.text_input("Jump to sample_id", "")
    if st.sidebar.button("Jump") and jump_sample:
        matched = merged.index[merged["sample_id"].astype(str) == jump_sample].tolist()
        if matched:
            st.session_state.market_state_index = int(matched[0])
            st.rerun()
        st.sidebar.warning(f"sample_id not found: {jump_sample}")

    row = merged.iloc[idx]
    try:
        window_df, target_local_idx = compute_chart_window(raw_df, str(row["timestamp"]), total_bars=total_bars)
        highlights = compute_layer_highlights(target_local_idx, row)
        fig = build_inspection_chart(window_df, target_local_idx, highlights)
    except Exception as exc:
        st.error(f"Chart build failed: {exc}")
        return

    st.plotly_chart(fig, width="stretch")

    st.caption(
        f"Rows={total} | current={idx + 1} | p3={row.get('pattern_3_actual_bars_used', '')} "
        f"m8={row.get('market_8_actual_bars_used', '')} m24={row.get('market_24_actual_bars_used', '')} "
        f"m128={row.get('market_128_actual_bars_used', '')} | confidence={row.get('structure_confidence', '')} | "
        "research-only, no LLM, no trading"
    )

    c_meta, c_rationale = st.columns([1, 1])
    with c_meta:
        st.subheader("Layer Metadata")
        st.json(
            {
                "sample_id": row.get("sample_id", ""),
                "timestamp": row.get("timestamp", ""),
                "pattern_3_event": row.get("pattern_3_event", ""),
                "market_8_state": row.get("market_8_state", ""),
                "market_24_state": row.get("market_24_state", ""),
                "market_128_state": row.get("market_128_state", ""),
                "local_structure_state": row.get("local_structure_state", ""),
                "structure_confidence": row.get("structure_confidence", ""),
                "actual_bars_used": {
                    "pattern_3": row.get("pattern_3_actual_bars_used", ""),
                    "market_8": row.get("market_8_actual_bars_used", ""),
                    "market_24": row.get("market_24_actual_bars_used", ""),
                    "market_128": row.get("market_128_actual_bars_used", ""),
                },
            }
        )
    with c_rationale:
        st.subheader("四层解释（中文）")
        st.markdown(f"**pattern_3**: {row.get('pattern_3_rationale_zh', '')}")
        st.markdown(f"**market_8**: {row.get('market_8_rationale_zh', '')}")
        st.markdown(f"**market_24**: {row.get('market_24_rationale_zh', '')}")
        st.markdown(f"**market_128**: {row.get('market_128_rationale_zh', '')}")
        st.markdown(f"**combined**: {row.get('market_state_rationale_zh', '')}")

    st.subheader("Manual Feedback")
    defaults = default_feedback_values(row)
    agree_opts = sorted(AGREEMENT_VALUES, key=lambda x: (x != "", x))
    hp3_agree = st.selectbox("human_pattern_3_agreement", agree_opts, index=agree_opts.index(defaults["human_pattern_3_agreement"]) if defaults["human_pattern_3_agreement"] in agree_opts else 0)
    hp3_correct = st.text_input("human_pattern_3_correct_label", value=defaults["human_pattern_3_correct_label"])
    hp3_fb = st.text_area("human_pattern_3_feedback_zh", value=defaults["human_pattern_3_feedback_zh"])

    hm8_agree = st.selectbox("human_market_8_agreement", agree_opts, index=agree_opts.index(defaults["human_market_8_agreement"]) if defaults["human_market_8_agreement"] in agree_opts else 0)
    hm8_correct = st.text_input("human_market_8_correct_state", value=defaults["human_market_8_correct_state"])
    hm8_fb = st.text_area("human_market_8_feedback_zh", value=defaults["human_market_8_feedback_zh"])

    hm24_agree = st.selectbox("human_market_24_agreement", agree_opts, index=agree_opts.index(defaults["human_market_24_agreement"]) if defaults["human_market_24_agreement"] in agree_opts else 0)
    hm24_correct = st.text_input("human_market_24_correct_state", value=defaults["human_market_24_correct_state"])
    hm24_fb = st.text_area("human_market_24_feedback_zh", value=defaults["human_market_24_feedback_zh"])

    hm128_agree = st.selectbox("human_market_128_agreement", agree_opts, index=agree_opts.index(defaults["human_market_128_agreement"]) if defaults["human_market_128_agreement"] in agree_opts else 0)
    hm128_correct = st.text_input("human_market_128_correct_state", value=defaults["human_market_128_correct_state"])
    hm128_fb = st.text_area("human_market_128_feedback_zh", value=defaults["human_market_128_feedback_zh"])

    hlocal_agree = st.selectbox("human_local_structure_agreement", agree_opts, index=agree_opts.index(defaults["human_local_structure_agreement"]) if defaults["human_local_structure_agreement"] in agree_opts else 0)
    hlocal_correct = st.text_input("human_local_structure_correct_state", value=defaults["human_local_structure_correct_state"])
    hlocal_fb = st.text_area("human_local_structure_feedback_zh", value=defaults["human_local_structure_feedback_zh"])

    hdef = st.text_area("human_definition_issue_zh", value=defaults["human_definition_issue_zh"])
    hrule = st.text_area("human_rule_adjustment_suggestion_zh", value=defaults["human_rule_adjustment_suggestion_zh"])

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

    c1, c2, c3, c4 = st.columns(4)
    if c1.button("Previous"):
        st.session_state.market_state_index = max(0, idx - 1)
        st.rerun()
    if c2.button("Save"):
        result = persist_feedback(payload, completed_csv=completed_csv, audit_jsonl=audit_jsonl)
        if result.get("status") == "ok":
            st.success(f"Saved sample_id={result['sample_id']}")
        else:
            st.error(f"Save blocked: {result.get('errors', [])}")
    if c3.button("Save and Next"):
        result = persist_feedback(payload, completed_csv=completed_csv, audit_jsonl=audit_jsonl)
        if result.get("status") == "ok":
            st.session_state.market_state_index = min(total - 1, idx + 1)
            st.rerun()
        st.error(f"Save blocked: {result.get('errors', [])}")
    if c4.button("Next"):
        st.session_state.market_state_index = min(total - 1, idx + 1)
        st.rerun()


if __name__ == "__main__":
    main()
