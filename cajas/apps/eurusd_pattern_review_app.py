"""EURUSD 15m pattern review GUI app."""
from pathlib import Path
from datetime import datetime

from cajas.research.eurusd_pattern_review_gui import (
    load_clean_view,
    load_review_batch,
    load_completed_reviews,
    load_label_schema,
    merge_completed_labels,
    extract_chart_window_with_diagnostics,
    create_candlestick_figure,
    build_compressed_gap_axis,
    summarize_compressed_gap_axis,
    get_chart_height,
    build_compact_chart_diagnostic_summary,
    build_chart_diagnostic_summary,
    save_review_action,
    clamp_sample_index,
    next_sample_index,
    previous_sample_index,
    load_rejected_samples,
    get_rejected_sample_ids,
    reject_sample_action,
    REJECT_REASON_OPTIONS,
    next_non_rejected_sample_index,
    previous_non_rejected_sample_index,
    should_advance_after_save,
    build_compact_save_feedback_message,
    default_review_values,
    get_review_progress,
    sanitize_optional_text_value,
    backup_active_review_persistence_files,
)

ACTIVE_REVIEW_APP_PATH = "cajas/apps/eurusd_pattern_review_app.py"
ACTIVE_REVIEW_LAUNCHER_PATH = "./scripts/run_eurusd_review_gui.sh"
OVERALL_REVIEW_FIELD_NAMES = [
    "human_label",
    "human_confidence",
    "human_rationale_zh",
    "human_counterexample_zh",
    "human_uncertainty_reason_zh",
    "human_context_notes_zh",
]
DETAIL_SECTION_NAMES = [
    "背景与走势 Context",
    "结构位置 Structure",
    "局部行为与确认 Behavior / Confirmation",
    "Sample-Level Review Summary",
    "候选归类 Candidate Family",
    "Notes",
]
PATTERN_3_DETAIL_FIELDS = [
    "human_pattern_3_agreement",
    "human_pattern_3_correct_label",
    "human_pattern_3_feedback_zh",
]
LOCAL_DETAIL_FIELDS = [
    "human_local_structure_agreement",
    "human_local_structure_correct_state",
    "human_local_structure_feedback_zh",
]
CANDIDATE_EXPLANATIONS_ZH = {
    "lower_wick_rejection_candidate": "下影线拒绝候选：目标K线出现下探后收回，需结合局部结构、短线背景和更大市场状态判断是否成立。",
    "upper_wick_rejection_candidate": "上影线拒绝候选：目标K线上探后回落，需结合局部结构、短线背景和更大市场状态判断是否成立。",
}


def render_plotly_chart(st_module, fig):
    """Render Plotly chart with new Streamlit width API and fallback."""
    try:
        st_module.plotly_chart(fig, width="stretch", theme=None)
    except TypeError:
        st_module.plotly_chart(fig, use_container_width=True, theme=None)


def build_compact_chart_status_line(base_line: str, axis_summary: dict) -> str:
    """Merge chart diagnostics and axis metadata into one compact line."""
    extra = [
        f"display_axis={axis_summary.get('display_axis', 'real_time_axis')}",
        f"time_gap_count={axis_summary.get('time_gap_count', 0)}",
    ]
    if axis_summary.get("time_gap_count", 0) > 0:
        extra.append(f"gap_markers={axis_summary.get('gap_markers', 0)}")
        extra.append(f"largest_gap_hours={axis_summary.get('largest_gap_hours', 0.0):.1f}")
    return f"{base_line} | " + " | ".join(extra)


def enqueue_pending_toast(state, message: str, kind: str = "success", icon: str = "✅") -> None:
    """Store one-shot toast payload to be consumed on next rerun."""
    state["pending_toast_message"] = message
    state["pending_toast_kind"] = kind
    state["pending_toast_icon"] = icon


def consume_pending_toast_once(st_module, state) -> None:
    """Display one-shot toast exactly once, then clear pending keys."""
    msg = state.pop("pending_toast_message", None)
    if not msg:
        state.pop("pending_toast_kind", None)
        state.pop("pending_toast_icon", None)
        return
    kind = state.pop("pending_toast_kind", "success")
    icon = state.pop("pending_toast_icon", "✅")
    if kind == "warning":
        st_module.sidebar.warning(msg)
        return
    if hasattr(st_module, "toast"):
        st_module.toast(msg, icon=icon)
    else:
        st_module.sidebar.success(msg)


def sample_number_to_global_index(sample_number: int, batch_count: int) -> int:
    """Convert 1-based sample number to clamped 0-based global index."""
    return clamp_sample_index(int(sample_number) - 1, batch_count)


def global_index_to_sample_number(global_index: int) -> int:
    """Convert 0-based global index to 1-based sample number."""
    return int(global_index) + 1


def apply_pending_global_sample_index(state, pending_key: str, current_key: str, input_key: str, batch_count: int) -> None:
    """Apply staged global sample navigation before rendering sample-dependent widgets."""
    if pending_key not in state:
        return
    idx = clamp_sample_index(int(state.pop(pending_key)), batch_count)
    state[current_key] = idx
    state[input_key] = global_index_to_sample_number(idx)


def apply_reject_form_sample_reset(state, sample_id: str) -> None:
    """Reset reject confirmation/notes when navigating to a different sample."""
    if state.pop("pending_clear_reject_confirm", False):
        state["confirm_reject_current_sample"] = False
    last_sample = str(state.get("reject_form_sample_id", ""))
    if last_sample != str(sample_id):
        state["confirm_reject_current_sample"] = False
        state["reject_notes"] = ""
        state["reject_form_sample_id"] = str(sample_id)


def inject_compact_review_css(st_module) -> None:
    """Hide unneeded Streamlit top chrome and compact header spacing for review workflow."""
    st_module.markdown(
        """
<style>
[data-testid="stHeader"] { display: none; }
[data-testid="stToolbar"] { display: none; }
[data-testid="stDecoration"] { display: none; }
#MainMenu { visibility: hidden; }
header { visibility: hidden; height: 0rem; }
.block-container { padding-top: 0.25rem; padding-bottom: 0.75rem; max-width: 1500px; }
h1, h2, h3 { margin-top: 0.1rem; margin-bottom: 0.35rem; }
[data-testid="stMetricValue"] { font-size: 1.4rem; }
[data-testid="stVerticalBlock"] { gap: 0.35rem; }
.stTextInput, .stSelectbox, .stTextArea { margin-bottom: 0.2rem; }
</style>
        """,
        unsafe_allow_html=True,
    )


def get_manual_feedback_layout_contract() -> dict:
    """Return an inspectable contract for the active manual-feedback render path."""
    return {
        "active_render_path_checked": True,
        "launcher_path": ACTIVE_REVIEW_LAUNCHER_PATH,
        "app_path": ACTIVE_REVIEW_APP_PATH,
        "render_entrypoint": "cajas.apps.eurusd_pattern_review_app.main",
        "manual_feedback_heading": "Manual Feedback",
        "candidate_context_heading": "Current Candidate / 当前候选",
        "candidate_context_visible": True,
        "candidate_type_visible": True,
        "candidate_type_source": "sample.candidate_type",
        "target_candle_context_visible": True,
        "candidate_context_field_names": [
            "sample_id",
            "candidate_type",
            "target_candle",
            "target_index",
            "standard_version",
            "candidate_type_explanation_zh",
        ],
        "candidate_context_before_overall_review": True,
        "layer_guide_visible": True,
        "layer_guide_lines": [
            "P3: target-near small pattern, roughly the smallest local candle combination.",
            "M8: short local rhythm/context around the target.",
            "M24: small swing / local regime context.",
            "M128: broader background context.",
            "Local: immediate local structure quality around the target candle; supports or weakens the current candidate but does not replace human_label.",
            "P3：目标K线附近最小形态。",
            "M8：短线节奏和附近结构。",
            "M24：小波段背景。",
            "M128：更大市场状态背景。",
            "Local：目标K线周围的局部结构质量，用来判断当前候选是否有局部支撑。",
        ],
        "overall_review_heading": "Overall Human Review / 总体人工审核",
        "overall_help_text": [
            "Overall fields are the final sample-level human decision.",
            "Layer tabs below are supporting detail only.",
            "human_label is the final sample-level review.",
            "P3/M8/M24/M128/Local fields are supporting layer feedback only.",
            "Local = local structure detail around the target candle. It helps explain the decision but does not replace human_label.",
            "human_label 是当前 candidate_type 的最终人工判断。",
            "Local/P3/M8/M24/M128 是证据层，不是最终结论。",
        ],
        "overall_field_names": list(OVERALL_REVIEW_FIELD_NAMES),
        "detail_group_heading": "Detailed Layer Feedback / 分层辅助反馈",
        "detail_ui_kind": "expanders",
        "detail_tab_names": list(DETAIL_SECTION_NAMES),
        "overall_review_section_visible": True,
        "overall_review_before_detail_tabs": True,
        "overall_fields_outside_detail_tabs": True,
        "pattern_3_is_detail_only": True,
        "local_is_detail_only": True,
        "pattern_3_detail_fields": list(PATTERN_3_DETAIL_FIELDS),
        "local_detail_fields": list(LOCAL_DETAIL_FIELDS),
        "market_state_tabbed_app_path": "cajas/apps/eurusd_market_state_inspection_app.py",
        "market_state_tabbed_app_is_active": False,
    }


def get_candidate_type_explanation_zh(candidate_type: str) -> str:
    """Return Chinese explanation for known candidate types, else empty string."""
    return CANDIDATE_EXPLANATIONS_ZH.get(str(candidate_type), "")


def main():
    try:
        import streamlit as st
    except ImportError:
        raise RuntimeError(
            "Streamlit is not available. Install with: ./.venv-qlib313/bin/python -m pip install streamlit plotly"
        )

    st.set_page_config(page_title="EURUSD 15m Review", layout="wide")
    inject_compact_review_css(st)
    CANONICAL_INDEX_KEY = "current_global_sample_idx"
    WIDGET_INDEX_KEY = "sample_number_input"
    PENDING_INDEX_KEY = "pending_global_sample_idx"

    consume_pending_toast_once(st, st.session_state)
    
    # Sidebar
    st.sidebar.header("Configuration")
    compact_mode = st.sidebar.checkbox("Compact mode", value=True)
    compact_chart_height = st.sidebar.slider(
        "Compact chart height",
        min_value=320,
        max_value=700,
        value=420,
        step=10,
    )
    
    clean_view_path = st.sidebar.text_input(
        "Clean View CSV",
        "tmp/eurusd/EURUSD_15m_Bid_clean_view.csv"
    )
    batch_path = st.sidebar.text_input(
        "Review Batch CSV",
        "tmp/eurusd/EURUSD_15m_pattern_review_batch_001.csv"
    )
    completed_path = st.sidebar.text_input(
        "Completed Output CSV",
        "tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed.csv"
    )
    events_jsonl_path = st.sidebar.text_input(
        "Review Events JSONL",
        "tmp/eurusd/EURUSD_15m_pattern_review_batch_001_completed_events.jsonl",
    )
    rejected_csv_path = st.sidebar.text_input(
        "Rejected Samples CSV",
        "tmp/eurusd/EURUSD_15m_pattern_review_rejected_samples.csv",
    )
    rejected_events_jsonl_path = st.sidebar.text_input(
        "Rejected Events JSONL",
        "tmp/eurusd/EURUSD_15m_pattern_review_rejected_samples_events.jsonl",
    )
    schema_path = st.sidebar.text_input(
        "Label Schema JSON",
        "tmp/validation-eurusd-pattern-label-schema.json"
    )
    if st.sidebar.button("Hard Reset Active Review Persistence"):
        reset_result = backup_active_review_persistence_files(
            completed_csv=Path(completed_path),
            events_jsonl=Path(events_jsonl_path),
            progress_json=Path("tmp/validation-eurusd-completed-review-progress.json"),
            progress_md=Path("tmp/validation-eurusd-completed-review-progress.md"),
            backup_root=Path("tmp/eurusd/review_schema_reset_backups"),
            stamp=datetime.now().strftime("%Y%m%d_%H%M%S"),
        )
        if reset_result.get("status") == "backed_up":
            st.sidebar.success(f"Backed up active artifacts to: {reset_result.get('backup_dir')}")
        else:
            st.sidebar.info("No active completed artifacts found to reset.")
        st.session_state.clear()
        st.rerun()
    
    if st.sidebar.button("Load/Reload"):
        st.session_state.clear()
    
    # Load data
    try:
        if "clean_view" not in st.session_state:
            st.session_state.clean_view = load_clean_view(Path(clean_view_path))
        if "batch" not in st.session_state:
            st.session_state.batch = load_review_batch(Path(batch_path))
        if "schema" not in st.session_state:
            st.session_state.schema = load_label_schema(Path(schema_path))
        
        completed = load_completed_reviews(Path(completed_path))
        st.session_state.batch = merge_completed_labels(st.session_state.batch, completed)
        st.session_state.rejected = load_rejected_samples(Path(rejected_csv_path))
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return
    
    batch = st.session_state.batch
    schema = st.session_state.schema
    
    # Filters
    st.sidebar.subheader("Filters")
    show_rejected_samples = st.sidebar.checkbox("Show rejected samples", value=False)
    
    candidate_types = ["All"] + sorted(batch["candidate_type"].unique().tolist())
    selected_type = st.sidebar.selectbox("Candidate Type", candidate_types)
    
    # Filter summary only; global sample navigation always uses full batch order.
    filtered = batch.copy()
    if selected_type != "All":
        filtered = filtered[filtered["candidate_type"] == selected_type]
    
    filtered_count = len(filtered)
    row_count = len(batch)
    sample_ids = batch["sample_id"].astype(str).tolist() if "sample_id" in batch.columns else []
    rejected_df = st.session_state.get("rejected")
    rejected_ids = get_rejected_sample_ids(rejected_df)

    # Migrate legacy key safely before widget instantiation.
    if "sample_idx" in st.session_state and CANONICAL_INDEX_KEY not in st.session_state:
        st.session_state[CANONICAL_INDEX_KEY] = st.session_state.get("sample_idx", 0)
    if "current_sample_idx" in st.session_state and CANONICAL_INDEX_KEY not in st.session_state:
        st.session_state[CANONICAL_INDEX_KEY] = st.session_state.get("current_sample_idx", 0)
    apply_pending_global_sample_index(
        st.session_state,
        pending_key=PENDING_INDEX_KEY,
        current_key=CANONICAL_INDEX_KEY,
        input_key=WIDGET_INDEX_KEY,
        batch_count=row_count,
    )
    if CANONICAL_INDEX_KEY not in st.session_state:
        st.session_state[CANONICAL_INDEX_KEY] = 0
    st.session_state[CANONICAL_INDEX_KEY] = clamp_sample_index(
        int(st.session_state.get(CANONICAL_INDEX_KEY, 0)),
        row_count,
    )
    if WIDGET_INDEX_KEY not in st.session_state:
        st.session_state[WIDGET_INDEX_KEY] = global_index_to_sample_number(st.session_state[CANONICAL_INDEX_KEY])
    
    # Sample selector
    st.sidebar.subheader("Sample")
    sample_number = st.sidebar.number_input(
        "Sample Number",
        min_value=1,
        max_value=row_count,
        key=WIDGET_INDEX_KEY
    )
    if st.sidebar.button("Go to Sample"):
        st.session_state[PENDING_INDEX_KEY] = sample_number_to_global_index(int(sample_number), row_count)
        st.rerun()
    st.sidebar.caption("Global position in full review batch; ignores filters.")
    sample_idx = int(st.session_state[CANONICAL_INDEX_KEY])
    st.sidebar.caption(f"Sample {global_index_to_sample_number(sample_idx)} / {row_count}")
    
    # Progress
    progress = get_review_progress(batch)
    st.sidebar.subheader("Progress")
    st.sidebar.caption(
        f"Reviewed {progress['reviewed']} / Total {progress['total']} | "
        f"Pending {progress['pending']} | Skipped {progress['skipped']} | Rejected {len(rejected_ids)}"
    )
    
    if selected_type != "All":
        st.sidebar.info(
            "Filters are active; direct Sample Number jump uses full batch order."
        )
        st.sidebar.caption(f"Filtered matches: {filtered_count}")
        st.sidebar.caption(
            f"Showing global sample {global_index_to_sample_number(sample_idx)}; current filters may not match this sample."
        )
    if filtered_count == 0:
        st.sidebar.warning("No rows match current filters; global sample display is unchanged.")

    # Current sample (always from full batch order)
    sample = batch.iloc[sample_idx]
    st.sidebar.caption(f"sample_id={sample['sample_id']} | global_index={sample_idx}")
    sample_id = str(sample["sample_id"])
    is_rejected_sample = sample_id in rejected_ids
    apply_reject_form_sample_reset(st.session_state, sample_id)
    if is_rejected_sample:
        st.sidebar.caption("Status: rejected/excluded")
    state_defaults = default_review_values()
    allowed = schema.get("allowed_values", {})
    review_key_map = {
        "market_context": "review_market_context",
        "trend_direction": "review_trend_direction",
        "trend_stage": "review_trend_stage",
        "volatility_state": "review_volatility_state",
        "recent_move_context": "review_recent_move_context",
        "session_context": "review_session_context",
        "structure_location": "review_structure_location",
        "level_quality": "review_level_quality",
        "local_behavior": "review_local_behavior",
        "confirmation_result": "review_confirmation_result",
        "human_label": "human_label",
        "human_confidence": "human_confidence",
        "review_outcome": "review_outcome",
        "pattern_quality": "pattern_quality",
        "false_positive_reason": "false_positive_reason",
        "review_confidence": "review_confidence",
        "primary_candidate_family": "primary_candidate_family",
        "secondary_candidate_family": "secondary_candidate_family",
        "review_notes": "review_notes",
        "human_rationale_zh": "human_rationale_zh",
        "human_counterexample_zh": "human_counterexample_zh",
        "human_uncertainty_reason_zh": "human_uncertainty_reason_zh",
        "human_context_notes_zh": "human_context_notes_zh",
    }

    if st.session_state.get("current_sample_id") != sample_id:
        st.session_state["current_sample_id"] = sample_id
        if is_rejected_sample and st.session_state.get("last_rejected_toast_sample_id") != sample_id:
            if hasattr(st, "toast"):
                st.toast("This sample is rejected/excluded.", icon="⛔")
            st.session_state["last_rejected_toast_sample_id"] = sample_id
        for field, key in review_key_map.items():
            value = sample.get(field, state_defaults[field])
            if field == "review_notes":
                value = sanitize_optional_text_value(value)
            st.session_state[key] = value if value not in (None, "") or field == "review_notes" else state_defaults[field]
        for text_field in [
            "review_notes",
            "human_rationale_zh",
            "human_counterexample_zh",
            "human_uncertainty_reason_zh",
            "human_context_notes_zh",
        ]:
            st.session_state[text_field] = sanitize_optional_text_value(st.session_state.get(text_field, ""))

    for field, key in review_key_map.items():
        if field in {"review_notes", "human_rationale_zh", "human_counterexample_zh", "human_uncertainty_reason_zh", "human_context_notes_zh"}:
            continue
        options = allowed.get(field)
        if isinstance(options, list) and options:
            if st.session_state.get(key) not in options:
                st.session_state[key] = options[0]

    st.markdown(
        f"#### EURUSD 15m Review · Sample {global_index_to_sample_number(sample_idx)}/{row_count} · Reviewed {progress['reviewed']}"
    )

    meta_line = " | ".join(
        [
            f"sample_id={sample['sample_id']}",
            f"timestamp={sample['timestamp']}",
            f"type={sample['candidate_type']}",
            f"confidence={sample['confidence_score']:.4f}",
            f"priority={sample['review_priority']}",
            f"reasons={sample['reason_codes']}",
        ]
    )
    with st.expander("Sample Details", expanded=False):
        st.caption(meta_line)

    # Chart
    chart_container = st.container()
    window, chart_diag = extract_chart_window_with_diagnostics(
        st.session_state.clean_view,
        sample["timestamp"],
        lookback=72,
        forward=48,
        pre_context_ratio=0.6,
        full_ohlc_source=st.session_state.clean_view,
    )

    fig = None
    chart_height = get_chart_height(compact_mode, compact_chart_height)
    if chart_diag.get("chart_window_row_count", 0) > 0:
        axis_info = build_compressed_gap_axis(window["timestamp"].tolist())
        axis_summary = summarize_compressed_gap_axis(axis_info)
        fig = create_candlestick_figure(
            window,
            sample["timestamp"],
            sample_id=str(sample["sample_id"]),
            candidate_type=str(sample["candidate_type"]),
            axis_info=axis_info,
        )
        if fig is not None:
            fig.update_layout(height=chart_height)
    else:
        axis_summary = summarize_compressed_gap_axis({"display_axis": "real_time_axis", "gaps": [], "gap_markers": []})

    with chart_container:
        if fig is None:
            if chart_diag.get("error"):
                st.warning(
                    f"Could not extract chart window for sample_id={sample['sample_id']} "
                    f"timestamp={sample['timestamp']}"
                )
            else:
                st.warning("No chart data available for the selected sample/timestamp.")
            if compact_mode:
                base = build_compact_chart_diagnostic_summary(chart_diag, trace_count=0)
            else:
                base = build_chart_diagnostic_summary(chart_diag, trace_count=0)
            st.caption(build_compact_chart_status_line(base, axis_summary))
            st.caption('Open "Chart Debug Info (click to expand)" for timestamp/window details.')
        else:
            render_plotly_chart(st, fig)
            if compact_mode:
                base = build_compact_chart_diagnostic_summary(chart_diag, trace_count=len(fig.data))
            else:
                base = build_chart_diagnostic_summary(chart_diag, trace_count=len(fig.data))
            st.caption(build_compact_chart_status_line(base, axis_summary))
    
    # Metadata
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.caption("Confidence")
        st.write(f"{sample['confidence_score']:.4f}")
    with m2:
        st.caption("Priority")
        st.write(str(sample["review_priority"]))
    with m3:
        st.caption("Candidate Type")
        st.write(str(sample["candidate_type"]))
    with m4:
        st.caption("Reason Codes")
        st.write(str(sample["reason_codes"]))
    
    # Compact lower layout: form on left, actions on right.
    left_col, right_col = st.columns([3.2, 1.4], gap="large")
    with left_col:
        st.markdown("#### Manual Feedback")
        st.caption("candidate_type 是系统入口标签，不是最终形态结论。")
        st.caption("Overall Human Review is the final sample-level decision.")
        st.caption("Detailed review fields below are supporting context, not a substitute for the final human label.")
        st.caption("`human_label` is the final sample-level human decision; `human_pattern_3_correct_label` is not used here as a substitute.")

        st.markdown("##### Current Candidate / 当前候选")
        candidate_type = str(sample.get("candidate_type", "unknown") or "unknown")
        candidate_explanation_zh = get_candidate_type_explanation_zh(candidate_type)
        target_timestamp = str(chart_diag.get("target_timestamp_used") or sample.get("timestamp") or "")
        target_index = chart_diag.get("target_index_global")
        st.caption(f"sample_id: {sample_id}")
        st.caption(f"candidate_type: {candidate_type}")
        st.caption(f"target candle: {target_timestamp}")
        st.caption(f"target_index: {target_index if target_index is not None else 'unknown'}")
        st.caption("standard_version: eurusd_15m_review_standard_v0")
        st.caption(f"你正在判断：当前样本是否构成 {candidate_type}。")
        if candidate_explanation_zh:
            st.caption(f"{candidate_type} = {candidate_explanation_zh}")

        st.markdown("##### Layer guide / 分层说明")
        st.caption("P3: target-near small pattern, roughly the smallest local candle combination.")
        st.caption("M8: short local rhythm/context around the target.")
        st.caption("M24: small swing / local regime context.")
        st.caption("M128: broader background context.")
        st.caption("Local: immediate local structure quality around the target candle; supports or weakens the current candidate but does not replace human_label.")
        st.caption("P3：目标K线附近最小形态。")
        st.caption("M8：短线节奏和附近结构。")
        st.caption("M24：小波段背景。")
        st.caption("M128：更大市场状态背景。")
        st.caption("Local：目标K线周围的局部结构质量，用来判断当前候选是否有局部支撑。")

        st.markdown("##### Overall Human Review / 总体人工审核")
        st.caption("Fill these overall fields before the more detailed review dimensions.")
        st.caption("Overall fields are the final sample-level human decision.")
        st.caption("Layer tabs below are supporting detail only.")
        st.caption("human_label is the final sample-level review.")
        st.caption("P3/M8/M24/M128/Local fields are supporting layer feedback only.")
        st.caption("human_label 是当前 candidate_type 的最终人工判断。")
        st.caption("Local/P3/M8/M24/M128 是证据层，不是最终结论。")
        overall_c1, overall_c2 = st.columns(2)
        with overall_c1:
            human_label = st.selectbox(
                "Overall human label / 总体人工判断",
                allowed.get("human_label", ["not_reviewed"]),
                key="human_label",
            )
        with overall_c2:
            human_confidence = st.selectbox(
                "Overall confidence / 总体置信度",
                allowed.get("human_confidence", ["not_reviewed"]),
                key="human_confidence",
            )

        human_rationale_zh = st.text_area(
            "Human rationale (ZH) / 人工判断理由",
            placeholder="填写中文的人审判断依据...",
            key="human_rationale_zh",
        )
        human_counterexample_zh = st.text_area(
            "Counterexample notes (ZH) / 反例/否定理由",
            placeholder="填写为什么该形态不成立或存在反例...",
            key="human_counterexample_zh",
        )
        human_uncertainty_reason_zh = st.text_area(
            "Uncertainty reason (ZH) / 不确定原因",
            placeholder="若不确定，填写不确定来源...",
            key="human_uncertainty_reason_zh",
        )
        human_context_notes_zh = st.text_area(
            "Context notes (ZH) / 上下文备注",
            placeholder="填写影响判断的上下文信息...",
            key="human_context_notes_zh",
        )

        st.markdown("##### Detailed Layer Feedback / 分层辅助反馈")
        st.caption("Use these fields as supporting review context after the overall human decision.")
        st.caption("Local = local structure detail around the target candle. It helps explain the decision but does not replace human_label.")
        st.caption("冲高回落/触底回升/急涨后整理/急跌后整理应填 recent_move_context，不要塞进 market_context。")
        st.caption("wick/doji 必须结合 structure_location 和 level_quality 判断。")
        st.caption("possible_false_breakout 必须看 level_quality、reclaim 和 follow-through。")

        with st.expander("背景与走势 Context", expanded=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                market_context = st.selectbox("market_context", allowed.get("market_context", ["unclear"]), key="review_market_context")
                trend_direction = st.selectbox("trend_direction", allowed.get("trend_direction", ["not_reviewed"]), key="review_trend_direction")
            with c2:
                trend_stage = st.selectbox("trend_stage", allowed.get("trend_stage", ["not_reviewed"]), key="review_trend_stage")
                volatility_state = st.selectbox("volatility_state", allowed.get("volatility_state", ["not_reviewed"]), key="review_volatility_state")
            with c3:
                recent_move_context = st.selectbox("recent_move_context", allowed.get("recent_move_context", ["not_reviewed"]), key="review_recent_move_context")
                session_context = st.selectbox("session_context", allowed.get("session_context", ["not_reviewed"]), key="review_session_context")

        with st.expander("结构位置 Structure", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                structure_location = st.selectbox("structure_location", allowed.get("structure_location", ["not_reviewed"]), key="review_structure_location")
            with c2:
                level_quality = st.selectbox("level_quality", allowed.get("level_quality", ["not_reviewed"]), key="review_level_quality")

        with st.expander("局部行为与确认 Behavior / Confirmation", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                local_behavior = st.selectbox("local_behavior", allowed.get("local_behavior", ["not_reviewed"]), key="review_local_behavior")
            with c2:
                confirmation_result = st.selectbox("confirmation_result", allowed.get("confirmation_result", ["not_reviewed"]), key="review_confirmation_result")

        with st.expander("Sample-Level Review Summary", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                pattern_quality = st.selectbox("pattern_quality", allowed.get("pattern_quality", ["not_reviewed"]), key="pattern_quality")
            with c2:
                false_positive_reason = st.selectbox("false_positive_reason", allowed.get("false_positive_reason", ["not_reviewed"]), key="false_positive_reason")

        with st.expander("候选归类 Candidate Family", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                primary_candidate_family = st.selectbox(
                    "primary_candidate_family",
                    allowed.get("primary_candidate_family", ["not_reviewed"]),
                    key="primary_candidate_family",
                )
            with c2:
                secondary_candidate_family = st.selectbox(
                    "secondary_candidate_family",
                    allowed.get("secondary_candidate_family", ["not_reviewed"]),
                    key="secondary_candidate_family",
                )
        review_notes = st.text_area(
            "review_notes",
            placeholder="Optional notes...",
            key="review_notes",
        )

        st.markdown("#### Bad Sample Workflow")
        reject_reason = st.selectbox("Reject Reason", REJECT_REASON_OPTIONS, key="reject_reason")
        reject_notes = st.text_input("Reject Notes", placeholder="Optional rejection notes...", key="reject_notes")
        confirm_reject = st.checkbox("Confirm reject current sample", key="confirm_reject_current_sample")

    def build_review_labels() -> dict:
        return {
            "market_context": market_context,
            "trend_direction": trend_direction,
            "trend_stage": trend_stage,
            "volatility_state": volatility_state,
            "recent_move_context": recent_move_context,
            "session_context": session_context,
            "structure_location": structure_location,
            "level_quality": level_quality,
            "local_behavior": local_behavior,
            "confirmation_result": confirmation_result,
            "human_label": human_label,
            "review_outcome": human_label,
            "pattern_quality": pattern_quality,
            "false_positive_reason": false_positive_reason,
            "human_confidence": human_confidence,
            "primary_candidate_family": primary_candidate_family,
            "secondary_candidate_family": secondary_candidate_family,
            "review_confidence": human_confidence,
            "review_notes": review_notes,
            "human_rationale_zh": human_rationale_zh,
            "human_counterexample_zh": human_counterexample_zh,
            "human_uncertainty_reason_zh": human_uncertainty_reason_zh,
            "human_context_notes_zh": human_context_notes_zh,
        }

    def persist_review(action_type: str, advance_to_next: bool) -> None:
        action = save_review_action(
            batch_df=batch,
            sample_id=sample_id,
            review_values=build_review_labels(),
            completed_csv_path=Path(completed_path),
            audit_jsonl_path=Path(events_jsonl_path),
            action_type=action_type,
            source_batch_path=batch_path,
        )
        st.session_state.batch = merge_completed_labels(
            st.session_state.batch, load_completed_reviews(Path(completed_path))
        )
        moved_to_idx = sample_idx
        if advance_to_next and should_advance_after_save(action):
            if show_rejected_samples:
                moved_to_idx = next_sample_index(sample_idx, row_count)
            else:
                moved_to_idx = next_non_rejected_sample_index(sample_idx, row_count, rejected_ids, sample_ids)
            st.session_state[PENDING_INDEX_KEY] = moved_to_idx
        current_idx = int(st.session_state.get(PENDING_INDEX_KEY, moved_to_idx))
        jsonl_status = "written" if action.get("jsonl_appended") else str(action.get("warning") or "not_written")
        feedback_message = build_compact_save_feedback_message(
            sample_id=sample_id,
            action_type=action_type,
            moved_to_human_index=(current_idx + 1) if action_type == "save_and_next" else None,
            total_count=row_count if action_type == "save_and_next" else None,
        )
        st.session_state["last_save_details"] = {
            "sample_id": sample_id,
            "action_type": action_type,
            "action_result": str(action.get("action_result", "unknown")),
            "completed_csv_path": completed_path,
            "jsonl_path": events_jsonl_path,
            "jsonl_status": jsonl_status,
            "sample_index": current_idx,
            "sample_number": global_index_to_sample_number(current_idx),
            "warning": action.get("warning"),
        }
        enqueue_pending_toast(
            st.session_state,
            feedback_message,
            kind="warning" if action.get("warning") else "success",
        )
        st.rerun()
    
    with right_col:
        st.markdown("#### Actions")
        st.caption("Use Save or Save and Next to persist edits before navigating.")

        if st.button("Save", use_container_width=True):
            try:
                persist_review(action_type="save", advance_to_next=False)
            except Exception as exc:
                st.error(f"Save failed for sample_id={sample_id}: {exc}")

        if st.button("Save and Next", use_container_width=True):
            try:
                persist_review(action_type="save_and_next", advance_to_next=True)
            except Exception as exc:
                st.error(f"Save and Next failed for sample_id={sample_id}: {exc}")

        nav1, nav2 = st.columns(2)
        with nav1:
            if st.button("Previous Sample", disabled=sample_idx <= 0, use_container_width=True):
                if show_rejected_samples:
                    st.session_state[PENDING_INDEX_KEY] = previous_sample_index(sample_idx, row_count)
                else:
                    st.session_state[PENDING_INDEX_KEY] = previous_non_rejected_sample_index(sample_idx, row_count, rejected_ids, sample_ids)
                st.rerun()
        with nav2:
            if st.button("Next Sample", disabled=sample_idx >= row_count - 1, use_container_width=True):
                if show_rejected_samples:
                    st.session_state[PENDING_INDEX_KEY] = next_sample_index(sample_idx, row_count)
                else:
                    st.session_state[PENDING_INDEX_KEY] = next_non_rejected_sample_index(sample_idx, row_count, rejected_ids, sample_ids)
                st.rerun()

        if st.button("Reject Sample", disabled=not confirm_reject, use_container_width=True):
            try:
                reject_action = reject_sample_action(
                    batch_df=batch,
                    sample_id=sample_id,
                    reason=reject_reason,
                    notes=reject_notes,
                    rejected_csv_path=Path(rejected_csv_path),
                    rejected_events_jsonl_path=Path(rejected_events_jsonl_path),
                    review_batch_id="eurusd_15m_pattern_review_batch_001",
                    source_batch_csv=batch_path,
                )
                st.session_state.rejected = load_rejected_samples(Path(rejected_csv_path))
                refreshed_rejected = get_rejected_sample_ids(st.session_state.rejected)
                next_idx = sample_idx
                if not show_rejected_samples:
                    next_idx = next_non_rejected_sample_index(sample_idx, row_count, refreshed_rejected, sample_ids)
                st.session_state[PENDING_INDEX_KEY] = next_idx
                st.session_state["pending_clear_reject_confirm"] = True
                enqueue_pending_toast(
                    st.session_state,
                    f"Rejected {sample_id} -> skipped from future review",
                    kind="warning" if reject_action.get("warning") else "success",
                    icon="⛔",
                )
                st.rerun()
            except Exception as exc:
                st.error(f"Reject failed for sample_id={sample_id}: {exc}")

    with st.expander("Last Save Details", expanded=False):
        st.json(st.session_state.get("last_save_details", {}))

    st.caption('Open "Chart Debug Info (click to expand)" for timestamp/window details.')
    with st.expander("Chart Debug Info (click to expand)", expanded=False):
        figure_meta = {}
        if fig is not None and getattr(fig.layout, "meta", None):
            figure_meta = dict(fig.layout.meta)
        st.json(
            {
                "sample_id": str(sample["sample_id"]),
                "selected_timestamp": str(sample["timestamp"]),
                "exact_timestamp_match_found": bool(chart_diag.get("exact_timestamp_match_found", False)),
                "nearest_fallback_used": bool(chart_diag.get("nearest_fallback_used", False)),
                "chart_window_row_count": int(chart_diag.get("chart_window_row_count", 0)),
                "target_index_in_window": chart_diag.get("target_index_in_window"),
                "source_target_index": chart_diag.get("target_index_global"),
                "window_start": chart_diag.get("window_start"),
                "window_end": chart_diag.get("window_end"),
                "window_bars": chart_diag.get("window_bars"),
                "pre_context_ratio": chart_diag.get("pre_context_ratio"),
                "sample_position_ratio": chart_diag.get("sample_position_ratio"),
                "boundary_clamp_start": chart_diag.get("boundary_clamp_start"),
                "boundary_clamp_end": chart_diag.get("boundary_clamp_end"),
                "full_source_row_count": chart_diag.get("full_source_row_count"),
                "chart_source_row_count": chart_diag.get("chart_source_row_count"),
                "source_min_timestamp": chart_diag.get("source_min_timestamp"),
                "source_max_timestamp": chart_diag.get("source_max_timestamp"),
                "sample_timestamp": chart_diag.get("sample_timestamp"),
                "sample_is_near_full_source_start": chart_diag.get("sample_is_near_full_source_start"),
                "framing_source_kind": chart_diag.get("framing_source_kind"),
                "sample_display_x": figure_meta.get("sample_display_x"),
                "sample_guide_line_x": figure_meta.get("sample_guide_line_x"),
                "sample_guide_line_offset": figure_meta.get("sample_guide_line_offset"),
                "sample_guide_line_side": figure_meta.get("sample_guide_line_side"),
                "sample_marker_mode": figure_meta.get("sample_marker_mode"),
                "figure_trace_count": int(len(fig.data)) if fig is not None else 0,
                "display_axis": axis_summary.get("display_axis"),
                "raw_time_axis_preserved_in_hover": axis_summary.get("raw_time_axis_preserved_in_hover"),
                "time_gap_count": axis_summary.get("time_gap_count"),
                "largest_gap_hours": axis_summary.get("largest_gap_hours"),
                "gap_markers": axis_summary.get("gap_markers"),
                "gaps": axis_summary.get("gaps"),
                "error": chart_diag.get("error"),
            }
        )


if __name__ == "__main__":
    main()
