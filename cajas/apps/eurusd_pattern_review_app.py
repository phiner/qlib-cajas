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
    CANONICAL_INDEX_KEY = "current_sample_idx"
    WIDGET_INDEX_KEY = "sample_idx_widget"
    PENDING_INDEX_KEY = "pending_sample_idx"
    
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
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return
    
    batch = st.session_state.batch
    schema = st.session_state.schema
    
    # Filters
    st.sidebar.subheader("Filters")
    
    candidate_types = ["All"] + sorted(batch["candidate_type"].unique().tolist())
    selected_type = st.sidebar.selectbox("Candidate Type", candidate_types)
    
    review_statuses = ["All", "pending", "reviewed"]
    selected_status = st.sidebar.selectbox("Review Status", review_statuses)
    
    # Filter batch
    filtered = batch.copy()
    if selected_type != "All":
        filtered = filtered[filtered["candidate_type"] == selected_type]
    if selected_status != "All":
        filtered = filtered[filtered["review_status"] == selected_status]
    
    if len(filtered) == 0:
        st.warning("No samples match filters")
        return
    row_count = len(filtered)

    # Migrate legacy key safely before widget instantiation.
    if "sample_idx" in st.session_state and CANONICAL_INDEX_KEY not in st.session_state:
        st.session_state[CANONICAL_INDEX_KEY] = st.session_state.get("sample_idx", 0)
    if PENDING_INDEX_KEY in st.session_state:
        st.session_state[CANONICAL_INDEX_KEY] = clamp_sample_index(
            int(st.session_state.pop(PENDING_INDEX_KEY)),
            row_count,
        )
    if CANONICAL_INDEX_KEY not in st.session_state:
        st.session_state[CANONICAL_INDEX_KEY] = 0
    st.session_state[CANONICAL_INDEX_KEY] = clamp_sample_index(
        int(st.session_state.get(CANONICAL_INDEX_KEY, 0)),
        row_count,
    )
    st.session_state[WIDGET_INDEX_KEY] = st.session_state[CANONICAL_INDEX_KEY]
    
    # Sample selector
    st.sidebar.subheader("Sample")
    sample_idx = st.sidebar.number_input(
        "Sample Index",
        min_value=0,
        max_value=row_count - 1,
        key=WIDGET_INDEX_KEY
    )
    st.session_state[CANONICAL_INDEX_KEY] = clamp_sample_index(int(sample_idx), row_count)
    sample_idx = st.session_state[CANONICAL_INDEX_KEY]
    
    # Progress
    progress = get_review_progress(batch)
    st.sidebar.subheader("Progress")
    st.sidebar.caption(
        f"Reviewed {progress['reviewed']} / Total {progress['total']} | "
        f"Pending {progress['pending']} | Skipped {progress['skipped']}"
    )
    
    # Current sample
    sample = filtered.iloc[sample_idx]
    sample_id = str(sample["sample_id"])
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
    if st.session_state.get("review_status") not in allowed.get("review_status", ["pending", "reviewed"]):
        st.session_state["review_status"] = allowed.get("review_status", ["pending", "reviewed"])[0]

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
        lookback=60,
        forward=30
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
            allowed.get("review_status", ["pending", "reviewed"]),
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
            allowed.get("review_status", ["pending", "reviewed"]),
            key="review_status",
        )
    
    # Save buttons
    st.caption("Use Save or Save and Next to persist edits before navigating.")
    col1, col2, col3, col4 = st.columns([1, 1.2, 1.2, 1])

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
            moved_to_idx = next_sample_index(sample_idx, row_count)
            st.session_state[PENDING_INDEX_KEY] = moved_to_idx
        current_idx = int(st.session_state.get(PENDING_INDEX_KEY, moved_to_idx))
        jsonl_status = "written" if action.get("jsonl_appended") else str(action.get("warning") or "not_written")
        st.session_state["last_action_msg"] = build_compact_save_feedback_message(
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
            "warning": action.get("warning"),
        }
        st.session_state["last_action_kind"] = "warning" if action.get("warning") else "success"
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
            st.session_state[PENDING_INDEX_KEY] = previous_sample_index(sample_idx, row_count)
            st.rerun()
    with col4:
        if st.button("Next Sample", disabled=sample_idx >= row_count - 1):
            st.session_state[PENDING_INDEX_KEY] = next_sample_index(sample_idx, row_count)
            st.rerun()

    if st.session_state.get("last_action_msg"):
        if st.session_state.get("last_action_kind") == "warning":
            st.sidebar.warning(st.session_state["last_action_msg"])
        else:
            if hasattr(st, "toast"):
                st.toast(st.session_state["last_action_msg"], icon="✅")
            else:
                st.sidebar.success(st.session_state["last_action_msg"])

    with st.expander("Last Save Details", expanded=False):
        st.json(st.session_state.get("last_save_details", {}))

    st.caption('Open "Chart Debug Info (click to expand)" for timestamp/window details.')
    with st.expander("Chart Debug Info (click to expand)", expanded=False):
        st.json(
            {
                "sample_id": str(sample["sample_id"]),
                "selected_timestamp": str(sample["timestamp"]),
                "exact_timestamp_match_found": bool(chart_diag.get("exact_timestamp_match_found", False)),
                "nearest_fallback_used": bool(chart_diag.get("nearest_fallback_used", False)),
                "chart_window_row_count": int(chart_diag.get("chart_window_row_count", 0)),
                "target_index_in_window": chart_diag.get("target_index_in_window"),
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
