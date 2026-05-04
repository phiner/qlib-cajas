"""EURUSD 15m pattern review GUI app."""
from pathlib import Path

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
)


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


def main():
    try:
        import streamlit as st
    except ImportError:
        raise RuntimeError(
            "Streamlit is not available. Install with: ./.venv-qlib313/bin/python -m pip install streamlit plotly"
        )

    st.set_page_config(page_title="EURUSD 15m Review", layout="wide")
    st.markdown(
        """
<style>
.block-container { padding-top: 1rem; padding-bottom: 1rem; max-width: 1500px; }
h1, h2, h3 { margin-top: 0.25rem; margin-bottom: 0.5rem; }
[data-testid="stMetricValue"] { font-size: 1.4rem; }
[data-testid="stVerticalBlock"] { gap: 0.4rem; }
.stTextInput, .stSelectbox, .stTextArea { margin-bottom: 0.25rem; }
</style>
        """,
        unsafe_allow_html=True,
    )
    st.title("EURUSD 15m Review")
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
    
    review_statuses = ["All"] + list(schema.get("allowed_values", {}).get("review_status", ["pending", "reviewed"]))
    selected_status = st.sidebar.selectbox("Review Status", review_statuses)
    
    # Filter summary only; global sample navigation always uses full batch order.
    filtered = batch.copy()
    if selected_type != "All":
        filtered = filtered[filtered["candidate_type"] == selected_type]
    if selected_status != "All":
        filtered = filtered[filtered["review_status"] == selected_status]
    
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
    
    if selected_type != "All" or selected_status != "All":
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
    if is_rejected_sample:
        st.warning("This sample is rejected/excluded.")
    state_defaults = default_review_values()
    allowed = schema.get("allowed_values", {})
    review_key_map = {
        "human_pattern_label": "review_pattern_label",
        "market_context": "review_market_context",
        "direction_context": "review_direction_context",
        "structure_quality": "review_structure_quality",
        "follow_through_quality": "review_follow_through_quality",
        "review_confidence": "review_confidence",
        "review_notes": "review_notes",
        "review_status": "review_status",
    }

    if st.session_state.get("current_sample_id") != sample_id:
        st.session_state["current_sample_id"] = sample_id
        for field, key in review_key_map.items():
            value = sample.get(field, state_defaults[field])
            if field == "review_notes":
                value = sanitize_optional_text_value(value)
            if field in {"structure_quality", "follow_through_quality", "review_confidence"}:
                value = int(value) if value is not None else int(state_defaults[field])
            st.session_state[key] = value if value not in (None, "") or field == "review_notes" else state_defaults[field]
        st.session_state["review_notes"] = sanitize_optional_text_value(st.session_state.get("review_notes", ""))

    if st.session_state.get("review_pattern_label") not in allowed.get("human_pattern_label", ["unclear"]):
        st.session_state["review_pattern_label"] = allowed.get("human_pattern_label", ["unclear"])[0]
    if st.session_state.get("review_market_context") not in allowed.get("market_context", ["unclear"]):
        st.session_state["review_market_context"] = allowed.get("market_context", ["unclear"])[0]
    if st.session_state.get("review_direction_context") not in allowed.get("direction_context", ["unclear"]):
        st.session_state["review_direction_context"] = allowed.get("direction_context", ["unclear"])[0]
    if st.session_state.get("review_status") not in allowed.get("review_status", ["pending", "reviewed", "needs_recheck", "skip"]):
        st.session_state["review_status"] = allowed.get("review_status", ["pending", "reviewed", "needs_recheck", "skip"])[0]

    if compact_mode:
        st.subheader(f"Sample {sample['sample_id']}")
    else:
        st.header(f"Sample: {sample['sample_id']}")
        st.subheader(f"{sample['timestamp']} - {sample['candidate_type']}")

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
    st.caption(meta_line)

    # Chart
    st.subheader("Candlestick Chart")
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
    
    # Review form
    st.subheader("Review Labels")

    top_cols = st.columns(4) if compact_mode else st.columns(2)
    col1 = top_cols[0]
    col2 = top_cols[1]
    col3 = top_cols[2] if compact_mode else top_cols[0]
    col4 = top_cols[3] if compact_mode else top_cols[1]
    
    with col1:
        human_pattern_label = st.selectbox(
            "Pattern Label",
            allowed.get("human_pattern_label", ["unclear"]),
            key="review_pattern_label",
        )
    with col2:
        market_context = st.selectbox(
            "Market Context",
            allowed.get("market_context", ["unclear"]),
            key="review_market_context",
        )
    with col3 if compact_mode else col1:
        direction_context = st.selectbox(
            "Direction Context",
            allowed.get("direction_context", ["unclear"]),
            key="review_direction_context",
        )

    if compact_mode:
        review_status = col4.selectbox(
            "Review Status",
            allowed.get("review_status", ["pending", "reviewed", "needs_recheck", "skip"]),
            key="review_status",
        )

    s_cols = st.columns(4) if compact_mode else st.columns(2)
    s1 = s_cols[0]
    s2 = s_cols[1]
    s3 = s_cols[2] if compact_mode else s_cols[0]
    s4 = s_cols[3] if compact_mode else s_cols[1]

    with s1:
        structure_quality = st.slider("Structure Quality", 1, 5, key="review_structure_quality")
    with s2:
        follow_through_quality = st.slider("Follow-through Quality", 1, 5, key="review_follow_through_quality")
    with s3 if compact_mode else s1:
        review_confidence = st.slider("Review Confidence", 1, 5, key="review_confidence")

    if compact_mode:
        with s4:
            review_notes = st.text_input(
                "Review Notes",
                placeholder="Optional notes...",
                key="review_notes",
            )
    else:
        review_notes = st.text_area(
            "Review Notes",
            placeholder="Optional notes...",
            key="review_notes",
        )
        review_status = st.selectbox(
            "Review Status",
            allowed.get("review_status", ["pending", "reviewed", "needs_recheck", "skip"]),
            key="review_status",
        )
    

    st.subheader("Bad Sample Workflow")
    reject_reason = st.selectbox("Reject Reason", REJECT_REASON_OPTIONS, key="reject_reason")
    reject_notes = st.text_input("Reject Notes", placeholder="Optional rejection notes...", key="reject_notes")
    confirm_reject = st.checkbox("Confirm reject current sample", key="confirm_reject_current_sample")

    # Save buttons
    st.caption("Use Save or Save and Next to persist edits before navigating.")
    col1, col2, col3, col4, col5 = st.columns([1, 1.2, 1.2, 1, 1.2])

    def build_review_labels() -> dict:
        return {
            "human_pattern_label": human_pattern_label,
            "market_context": market_context,
            "direction_context": direction_context,
            "structure_quality": structure_quality,
            "follow_through_quality": follow_through_quality,
            "review_confidence": review_confidence,
            "review_notes": review_notes,
            "review_status": review_status,
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
    
    with col1:
        if st.button("Save"):
            try:
                persist_review(action_type="save", advance_to_next=False)
            except Exception as exc:
                st.error(f"Save failed for sample_id={sample_id}: {exc}")
    
    with col2:
        if st.button("Save and Next"):
            try:
                persist_review(action_type="save_and_next", advance_to_next=True)
            except Exception as exc:
                st.error(f"Save and Next failed for sample_id={sample_id}: {exc}")
    
    with col3:
        if st.button("Previous Sample", disabled=sample_idx <= 0):
            if show_rejected_samples:
                st.session_state[PENDING_INDEX_KEY] = previous_sample_index(sample_idx, row_count)
            else:
                st.session_state[PENDING_INDEX_KEY] = previous_non_rejected_sample_index(sample_idx, row_count, rejected_ids, sample_ids)
            st.rerun()
    with col4:
        if st.button("Next Sample", disabled=sample_idx >= row_count - 1):
            if show_rejected_samples:
                st.session_state[PENDING_INDEX_KEY] = next_sample_index(sample_idx, row_count)
            else:
                st.session_state[PENDING_INDEX_KEY] = next_non_rejected_sample_index(sample_idx, row_count, rejected_ids, sample_ids)
            st.rerun()


    with col5:
        if st.button("Reject Sample", disabled=not confirm_reject):
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
