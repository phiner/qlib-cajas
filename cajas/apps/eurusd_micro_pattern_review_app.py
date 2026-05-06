"""Dedicated EURUSD micro-pattern packet review app."""

from __future__ import annotations

from pathlib import Path

from cajas.research.eurusd_micro_pattern_review_gui import (
    CONFIDENCE_OPTIONS,
    LABEL_OPTIONS,
    SHOULD_CREATE_RULE_OPTIONS,
    default_micro_pattern_label_values,
    load_completed_micro_pattern_labels,
    load_micro_pattern_packet,
    merge_packet_with_completed_labels,
    persist_micro_pattern_label,
)


def main() -> None:
    try:
        import streamlit as st
    except ImportError as exc:
        raise RuntimeError(
            "Streamlit is not available. Install with: ./.venv-qlib313/bin/python -m pip install streamlit"
        ) from exc

    st.set_page_config(page_title="EURUSD Micro Pattern Packet Labeling", layout="wide")
    st.title("EURUSD Micro Pattern Packet Labeling")

    st.sidebar.header("Paths")
    packet_csv = Path(
        st.sidebar.text_input(
            "Packet CSV",
            "tmp/eurusd/EURUSD_15m_micro_pattern_review_packet.csv",
        )
    )
    completed_csv = Path(
        st.sidebar.text_input(
            "Completed Labels CSV",
            "tmp/eurusd/EURUSD_15m_micro_pattern_review_packet_completed_template.csv",
        )
    )
    audit_jsonl = Path(
        st.sidebar.text_input(
            "Audit JSONL",
            "tmp/eurusd/EURUSD_15m_micro_pattern_review_events.jsonl",
        )
    )

    try:
        packet = load_micro_pattern_packet(packet_csv)
        completed = load_completed_micro_pattern_labels(completed_csv)
        merged = merge_packet_with_completed_labels(packet, completed)
    except Exception as exc:
        st.error(f"Failed to load packet data: {exc}")
        return

    if merged.empty:
        st.warning("Packet has no rows.")
        return

    total = len(merged)
    if "micro_packet_index" not in st.session_state:
        st.session_state.micro_packet_index = 0

    jump_sample = st.sidebar.text_input("Jump to sample_id", "")
    if st.sidebar.button("Jump"):
        if jump_sample:
            matched = merged.index[merged["sample_id"].astype(str) == jump_sample].tolist()
            if matched:
                st.session_state.micro_packet_index = int(matched[0])
            else:
                st.sidebar.warning(f"sample_id not found: {jump_sample}")

    idx = max(0, min(int(st.session_state.micro_packet_index), total - 1))
    row = merged.iloc[idx]
    st.subheader(f"Row {idx + 1}/{total} - sample_id={row['sample_id']}")
    st.caption(
        f"timestamp={row.get('timestamp', '')} | event={row.get('micro_pattern_event_3', '')} | "
        f"noise_subtype={row.get('micro_noise_subtype', '')} | rule_version={row.get('micro_pattern_rule_version', '')}"
    )

    ohlc_fields = [
        "bar_t_minus_2_open",
        "bar_t_minus_2_high",
        "bar_t_minus_2_low",
        "bar_t_minus_2_close",
        "bar_t_minus_1_open",
        "bar_t_minus_1_high",
        "bar_t_minus_1_low",
        "bar_t_minus_1_close",
        "bar_t_open",
        "bar_t_high",
        "bar_t_low",
        "bar_t_close",
    ]
    st.markdown("**3-Bar OHLC Context**")
    st.dataframe(row[ohlc_fields].to_frame(name="value"), use_container_width=True)
    st.markdown("**Metrics**")
    st.write(
        {
            "three_bar_return": row.get("three_bar_return", ""),
            "latest_close_position_in_candle": row.get("latest_close_position_in_candle", ""),
            "latest_close_position_in_three_bar_range": row.get("latest_close_position_in_three_bar_range", ""),
        }
    )

    defaults = default_micro_pattern_label_values(row)
    label = st.selectbox(
        "human_micro_pattern_label",
        options=[""] + LABEL_OPTIONS,
        index=([""] + LABEL_OPTIONS).index(defaults["human_micro_pattern_label"])
        if defaults["human_micro_pattern_label"] in ([""] + LABEL_OPTIONS)
        else 0,
    )
    confidence = st.selectbox(
        "human_micro_pattern_confidence",
        options=[""] + CONFIDENCE_OPTIONS,
        index=([""] + CONFIDENCE_OPTIONS).index(defaults["human_micro_pattern_confidence"])
        if defaults["human_micro_pattern_confidence"] in ([""] + CONFIDENCE_OPTIONS)
        else 0,
    )
    rationale = st.text_area("human_micro_pattern_rationale_zh", value=defaults["human_micro_pattern_rationale_zh"])
    rule_suggestion = st.text_area("human_rule_suggestion_zh", value=defaults["human_rule_suggestion_zh"])
    should_create = st.selectbox(
        "human_should_create_rule",
        options=[""] + SHOULD_CREATE_RULE_OPTIONS,
        index=([""] + SHOULD_CREATE_RULE_OPTIONS).index(defaults["human_should_create_rule"])
        if defaults["human_should_create_rule"] in ([""] + SHOULD_CREATE_RULE_OPTIONS)
        else 0,
    )
    event_key = st.text_input("suggested_event_key", value=defaults["suggested_event_key"])

    c1, c2, c3, c4 = st.columns(4)
    if c1.button("Previous"):
        st.session_state.micro_packet_index = max(0, idx - 1)
        st.rerun()
    if c2.button("Save"):
        result = persist_micro_pattern_label(
            {
                **row.to_dict(),
                "human_micro_pattern_label": label,
                "human_micro_pattern_confidence": confidence,
                "human_micro_pattern_rationale_zh": rationale,
                "human_rule_suggestion_zh": rule_suggestion,
                "human_should_create_rule": should_create,
                "suggested_event_key": event_key,
            },
            completed_csv=completed_csv,
            audit_jsonl=audit_jsonl,
        )
        if result.get("status") == "ok":
            st.success(f"Saved sample_id={result['sample_id']}")
        else:
            st.error(f"Save blocked: {result.get('errors', [])}")
    if c3.button("Save and Next"):
        result = persist_micro_pattern_label(
            {
                **row.to_dict(),
                "human_micro_pattern_label": label,
                "human_micro_pattern_confidence": confidence,
                "human_micro_pattern_rationale_zh": rationale,
                "human_rule_suggestion_zh": rule_suggestion,
                "human_should_create_rule": should_create,
                "suggested_event_key": event_key,
            },
            completed_csv=completed_csv,
            audit_jsonl=audit_jsonl,
        )
        if result.get("status") == "ok":
            st.session_state.micro_packet_index = min(total - 1, idx + 1)
            st.rerun()
        st.error(f"Save blocked: {result.get('errors', [])}")
    if c4.button("Next"):
        st.session_state.micro_packet_index = min(total - 1, idx + 1)
        st.rerun()


if __name__ == "__main__":
    main()
