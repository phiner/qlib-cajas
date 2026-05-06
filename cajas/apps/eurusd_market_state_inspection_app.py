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
REVIEW_LAYOUT_COLUMN_RATIO = [4, 1]


def main() -> None:
    try:
        import streamlit as st
    except ImportError as exc:
        raise RuntimeError(
            "Streamlit is not available. Install with: ./.venv-qlib313/bin/python -m pip install streamlit plotly"
        ) from exc

    st.set_page_config(page_title="EURUSD Market-state Inspection", layout="wide")
    st.markdown(
        """
<style>
.msi-title { font-size: 30px; font-weight: 700; margin-bottom: 0.2rem; }
.msi-sub { font-size: 17px; color: #334155; margin-bottom: 0.6rem; }
.msi-chip { font-size: 17px; font-weight: 600; }
.msi-section { font-size: 23px; font-weight: 700; margin-top: 0.4rem; }
.msi-rationale { font-size: 16px; line-height: 1.45; margin-bottom: 0.4rem; }
.msi-small { font-size: 15px; color: #475569; }
div[data-testid="stDataFrame"] * { font-size: 16px !important; }
label[data-testid="stWidgetLabel"] p { font-size: 16px !important; font-weight: 600 !important; }
textarea, input, select { font-size: 16px !important; }
</style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="msi-title">EURUSD 四层市场状态图表审阅</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="msi-sub">chart + feedback simultaneous review · research-only · no LLM · no trading</div>',
        unsafe_allow_html=True,
    )

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

    controls = st.columns([1.2, 1.5, 0.9, 0.9, 1.6, 0.9, 1.1, 1.1])
    controls[0].markdown(f'<div class="msi-chip">Sample {idx + 1}/{total}</div>', unsafe_allow_html=True)
    controls[1].markdown(
        f'<div class="msi-chip">confidence: {row.get("structure_confidence", "")}</div>',
        unsafe_allow_html=True,
    )
    if controls[2].button("Previous", use_container_width=True):
        st.session_state.market_state_index = max(0, idx - 1)
        st.rerun()
    if controls[3].button("Next", use_container_width=True):
        st.session_state.market_state_index = min(total - 1, idx + 1)
        st.rerun()
    jump_sample = controls[4].text_input(
        "Jump sample_id", key="market_state_jump_input", label_visibility="collapsed", placeholder="sample_id"
    )
    if controls[5].button("Jump", use_container_width=True) and jump_sample:
        matched = merged.index[merged["sample_id"].astype(str) == jump_sample].tolist()
        if matched:
            st.session_state.market_state_index = int(matched[0])
            st.rerun()
        st.warning(f"sample_id not found: {jump_sample}")
    save_now = controls[6].button("Save", use_container_width=True)
    save_next = controls[7].button("Save+Next", use_container_width=True)

    left, right = st.columns(REVIEW_LAYOUT_COLUMN_RATIO, gap="large")
    try:
        window_df, target_local_idx = compute_chart_window(raw_df, str(row["timestamp"]), total_bars=total_bars)
        highlights = compute_layer_highlights(target_local_idx, row)
        fig = build_inspection_chart(window_df, target_local_idx, highlights)
    except Exception as exc:
        st.error(f"Chart build failed: {exc}")
        return

    with left:
        st.plotly_chart(fig, width="stretch", height=620)
        st.markdown('<div class="msi-small">compressed axis + weekend/market-closed gap markers + explicit 3/8/24/128 spans</div>', unsafe_allow_html=True)
        st.markdown('<div class="msi-section">Layer Summary</div>', unsafe_allow_html=True)
        st.dataframe(build_layer_summary(row), hide_index=True, width="stretch")
        st.markdown('<div class="msi-section">Rationale</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="msi-rationale"><b>pattern_3</b>: {row.get("pattern_3_rationale_zh", "")}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="msi-rationale"><b>market_8</b>: {row.get("market_8_rationale_zh", "")}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="msi-rationale"><b>market_24</b>: {row.get("market_24_rationale_zh", "")}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="msi-rationale"><b>market_128</b>: {row.get("market_128_rationale_zh", "")}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="msi-rationale"><b>combined</b>: {row.get("market_state_rationale_zh", "")}</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="msi-section">Manual Feedback</div>', unsafe_allow_html=True)
        defaults = default_feedback_values(row)
        agree_opts = sorted(AGREEMENT_VALUES, key=lambda x: (x != "", x))

        tabs = st.tabs(["P3", "M8", "M24", "M128", "Local", "Notes"])
        with tabs[0]:
            hp3_agree = st.selectbox("human_pattern_3_agreement", agree_opts, index=agree_opts.index(defaults["human_pattern_3_agreement"]) if defaults["human_pattern_3_agreement"] in agree_opts else 0, key="p3_agree")
            hp3_correct = st.text_input("human_pattern_3_correct_label", value=defaults["human_pattern_3_correct_label"], key="p3_correct")
            hp3_fb = st.text_area("human_pattern_3_feedback_zh", value=defaults["human_pattern_3_feedback_zh"], height=90, key="p3_fb")
        with tabs[1]:
            hm8_agree = st.selectbox("human_market_8_agreement", agree_opts, index=agree_opts.index(defaults["human_market_8_agreement"]) if defaults["human_market_8_agreement"] in agree_opts else 0, key="m8_agree")
            hm8_correct = st.text_input("human_market_8_correct_state", value=defaults["human_market_8_correct_state"], key="m8_correct")
            hm8_fb = st.text_area("human_market_8_feedback_zh", value=defaults["human_market_8_feedback_zh"], height=90, key="m8_fb")
        with tabs[2]:
            hm24_agree = st.selectbox("human_market_24_agreement", agree_opts, index=agree_opts.index(defaults["human_market_24_agreement"]) if defaults["human_market_24_agreement"] in agree_opts else 0, key="m24_agree")
            hm24_correct = st.text_input("human_market_24_correct_state", value=defaults["human_market_24_correct_state"], key="m24_correct")
            hm24_fb = st.text_area("human_market_24_feedback_zh", value=defaults["human_market_24_feedback_zh"], height=90, key="m24_fb")
        with tabs[3]:
            hm128_agree = st.selectbox("human_market_128_agreement", agree_opts, index=agree_opts.index(defaults["human_market_128_agreement"]) if defaults["human_market_128_agreement"] in agree_opts else 0, key="m128_agree")
            hm128_correct = st.text_input("human_market_128_correct_state", value=defaults["human_market_128_correct_state"], key="m128_correct")
            hm128_fb = st.text_area("human_market_128_feedback_zh", value=defaults["human_market_128_feedback_zh"], height=90, key="m128_fb")
        with tabs[4]:
            hlocal_agree = st.selectbox("human_local_structure_agreement", agree_opts, index=agree_opts.index(defaults["human_local_structure_agreement"]) if defaults["human_local_structure_agreement"] in agree_opts else 0, key="local_agree")
            hlocal_correct = st.text_input("human_local_structure_correct_state", value=defaults["human_local_structure_correct_state"], key="local_correct")
            hlocal_fb = st.text_area("human_local_structure_feedback_zh", value=defaults["human_local_structure_feedback_zh"], height=90, key="local_fb")
        with tabs[5]:
            hdef = st.text_area("human_definition_issue_zh", value=defaults["human_definition_issue_zh"], height=100)
            hrule = st.text_area("human_rule_adjustment_suggestion_zh", value=defaults["human_rule_adjustment_suggestion_zh"], height=100)

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

    if save_now:
        result = persist_feedback(payload, completed_csv=completed_csv, audit_jsonl=audit_jsonl)
        if result.get("status") == "ok":
            st.success(f"Saved sample_id={result['sample_id']}")
        else:
            st.error(f"Save blocked: {result.get('errors', [])}")
    if save_next:
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
