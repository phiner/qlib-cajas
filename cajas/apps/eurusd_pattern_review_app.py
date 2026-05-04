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
    get_chart_height,
    build_compact_chart_diagnostic_summary,
    build_chart_diagnostic_summary,
    save_or_update_completed_review,
    append_review_event_jsonl,
    build_persistence_status_message,
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
    
    # Sample selector
    st.sidebar.subheader("Sample")
    if "sample_idx" not in st.session_state:
        st.session_state.sample_idx = 0
    sample_idx = st.sidebar.number_input(
        "Sample Index",
        min_value=0,
        max_value=len(filtered) - 1,
        key="sample_idx"
    )
    
    # Progress
    progress = get_review_progress(batch)
    st.sidebar.subheader("Progress")
    st.sidebar.caption(
        f"Reviewed {progress['reviewed']} / Total {progress['total']} | "
        f"Pending {progress['pending']} | Skipped {progress['skipped']}"
    )
    
    # Current sample
    sample = filtered.iloc[int(sample_idx)]
    sample_id = str(sample["sample_id"])
    state_defaults = default_review_values()
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
        fig = create_candlestick_figure(
            window,
            sample["timestamp"],
            sample_id=str(sample["sample_id"]),
            candidate_type=str(sample["candidate_type"]),
        )
        if fig is not None:
            fig.update_layout(height=chart_height)

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
                st.caption(build_compact_chart_diagnostic_summary(chart_diag, trace_count=0))
            else:
                st.caption(build_chart_diagnostic_summary(chart_diag, trace_count=0))
            st.caption('Open "Chart Debug Info (click to expand)" for timestamp/window details.')
        else:
            render_plotly_chart(st, fig)
            if compact_mode:
                st.caption(build_compact_chart_diagnostic_summary(chart_diag, trace_count=len(fig.data)))
            else:
                st.caption(build_chart_diagnostic_summary(chart_diag, trace_count=len(fig.data)))
    
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
    
    allowed = schema.get("allowed_values", {})
    
    top_cols = st.columns(4) if compact_mode else st.columns(2)
    col1 = top_cols[0]
    col2 = top_cols[1]
    col3 = top_cols[2] if compact_mode else top_cols[0]
    col4 = top_cols[3] if compact_mode else top_cols[1]
    
    with col1:
        human_pattern_label = st.selectbox(
            "Pattern Label",
            allowed.get("human_pattern_label", ["unclear"]),
            index=allowed.get("human_pattern_label", ["unclear"]).index(
                st.session_state.get("review_pattern_label", "unclear")
            ) if st.session_state.get("review_pattern_label") in allowed.get("human_pattern_label", []) else 0,
            key="review_pattern_label",
        )
    with col2:
        market_context = st.selectbox(
            "Market Context",
            allowed.get("market_context", ["unclear"]),
            index=allowed.get("market_context", ["unclear"]).index(
                st.session_state.get("review_market_context", "unclear")
            ) if st.session_state.get("review_market_context") in allowed.get("market_context", []) else 0,
            key="review_market_context",
        )
    with col3 if compact_mode else col1:
        direction_context = st.selectbox(
            "Direction Context",
            allowed.get("direction_context", ["unclear"]),
            index=allowed.get("direction_context", ["unclear"]).index(
                st.session_state.get("review_direction_context", "unclear")
            ) if st.session_state.get("review_direction_context") in allowed.get("direction_context", []) else 0,
            key="review_direction_context",
        )

    if compact_mode:
        review_status = col4.selectbox(
            "Review Status",
            allowed.get("review_status", ["pending", "reviewed"]),
            index=allowed.get("review_status", ["pending"]).index(
                st.session_state.get("review_status", "pending")
            ) if st.session_state.get("review_status") in allowed.get("review_status", []) else 0,
            key="review_status",
        )

    s_cols = st.columns(4) if compact_mode else st.columns(2)
    s1 = s_cols[0]
    s2 = s_cols[1]
    s3 = s_cols[2] if compact_mode else s_cols[0]
    s4 = s_cols[3] if compact_mode else s_cols[1]

    with s1:
        structure_quality = st.slider("Structure Quality", 1, 5, int(st.session_state.get("review_structure_quality", 3)), key="review_structure_quality")
    with s2:
        follow_through_quality = st.slider("Follow-through Quality", 1, 5, int(st.session_state.get("review_follow_through_quality", 3)), key="review_follow_through_quality")
    with s3 if compact_mode else s1:
        review_confidence = st.slider("Review Confidence", 1, 5, int(st.session_state.get("review_confidence", 3)), key="review_confidence")

    if compact_mode:
        with s4:
            review_notes = st.text_input(
                "Review Notes",
                value=sanitize_optional_text_value(st.session_state.get("review_notes", "")),
                placeholder="Optional notes...",
                key="review_notes",
            )
    else:
        review_notes = st.text_area(
            "Review Notes",
            sanitize_optional_text_value(st.session_state.get("review_notes", "")),
            placeholder="Optional notes...",
            key="review_notes",
        )
        review_status = st.selectbox(
            "Review Status",
            allowed.get("review_status", ["pending", "reviewed"]),
            index=allowed.get("review_status", ["pending"]).index(
                st.session_state.get("review_status", "pending")
            ) if st.session_state.get("review_status") in allowed.get("review_status", []) else 0,
            key="review_status",
        )
    
    # Save buttons
    col1, col2, col3 = st.columns(3)
    
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
        if st.button("Reset Form"):
            defaults = default_review_values()
            for field, key in review_key_map.items():
                st.session_state[key] = defaults[field]
            st.session_state["last_action_msg"] = f"Form reset for sample_id={sample_id}"
            st.rerun()

    if st.session_state.get("last_action_msg"):
        if st.session_state.get("last_action_kind") == "warning":
            st.warning(st.session_state["last_action_msg"])
        else:
            st.success(st.session_state["last_action_msg"])

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
                "error": chart_diag.get("error"),
            }
        )


if __name__ == "__main__":
    main()
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
        labels = build_review_labels()
        result = save_or_update_completed_review(batch, sample_id, labels, Path(completed_path))
        st.session_state.batch = merge_completed_labels(
            st.session_state.batch, load_completed_reviews(Path(completed_path))
        )
        jsonl_status = "written"
        try:
            append_review_event_jsonl(
                jsonl_path=Path(events_jsonl_path),
                sample_id=sample_id,
                review_values=labels,
                action_type=action_type,
                completed_csv_path=Path(completed_path),
                batch_path=batch_path,
            )
        except Exception as jsonl_exc:
            jsonl_status = f"error: {jsonl_exc}"
        if advance_to_next and int(sample_idx) < len(filtered) - 1:
            st.session_state.sample_idx = int(sample_idx) + 1
        current_idx = int(st.session_state.get("sample_idx", int(sample_idx)))
        st.session_state["last_action_msg"] = build_persistence_status_message(
            sample_id=sample_id,
            action_result=result["action_result"],
            action_type=action_type,
            completed_csv_path=completed_path,
            jsonl_path=events_jsonl_path,
            jsonl_status=jsonl_status,
            sample_index=current_idx,
        )
        if jsonl_status != "written":
            st.session_state["last_action_kind"] = "warning"
        else:
            st.session_state["last_action_kind"] = "success"
        st.rerun()
