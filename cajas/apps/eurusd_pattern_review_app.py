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
    save_completed_review,
    get_review_progress,
    sanitize_optional_text_value,
)


def main():
    try:
        import streamlit as st
    except ImportError:
        raise RuntimeError(
            "Streamlit is not available. Install with: ./.venv-qlib313/bin/python -m pip install streamlit plotly"
        )

    st.set_page_config(page_title="EURUSD Pattern Review", layout="wide")
    st.title("EURUSD 15m Pattern Review")
    
    # Sidebar
    st.sidebar.header("Configuration")
    
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
    st.sidebar.header("Filters")
    
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
    st.sidebar.header("Sample Navigation")
    sample_idx = st.sidebar.number_input(
        "Sample Index",
        min_value=0,
        max_value=len(filtered) - 1,
        value=0
    )
    
    # Progress
    progress = get_review_progress(batch)
    st.sidebar.header("Progress")
    st.sidebar.metric("Total", progress["total"])
    st.sidebar.metric("Reviewed", progress["reviewed"])
    st.sidebar.metric("Pending", progress["pending"])
    st.sidebar.metric("Skipped", progress["skipped"])
    
    # Current sample
    sample = filtered.iloc[sample_idx]

    st.header(f"Sample: {sample['sample_id']}")
    st.subheader(f"{sample['timestamp']} - {sample['candidate_type']}")

    # Sample metadata near chart
    st.caption(
        " | ".join(
            [
                f"sample_id={sample['sample_id']}",
                f"timestamp={sample['timestamp']}",
                f"candidate_type={sample['candidate_type']}",
                f"confidence_score={sample['confidence_score']:.4f}",
                f"review_priority={sample['review_priority']}",
                f"reason_codes={sample['reason_codes']}",
            ]
        )
    )

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
    if chart_diag.get("chart_window_row_count", 0) > 0:
        fig = create_candlestick_figure(
            window,
            sample["timestamp"],
            sample_id=str(sample["sample_id"]),
            candidate_type=str(sample["candidate_type"]),
        )

    with chart_container:
        if fig is None:
            if chart_diag.get("error"):
                st.warning(
                    f"Could not extract chart window for sample_id={sample['sample_id']} "
                    f"timestamp={sample['timestamp']}"
                )
            else:
                st.warning("No chart data available for the selected sample/timestamp.")
        else:
            st.plotly_chart(fig, use_container_width=True, theme=None)

    with st.expander("Chart Debug Info", expanded=False):
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
    
    # Metadata
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Confidence Score", f"{sample['confidence_score']:.4f}")
        st.metric("Review Priority", sample["review_priority"])
    with col2:
        st.text(f"Reason Codes: {sample['reason_codes']}")
    
    # Review form
    st.header("Review Labels")
    
    allowed = schema.get("allowed_values", {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        human_pattern_label = st.selectbox(
            "Pattern Label",
            allowed.get("human_pattern_label", ["unclear"]),
            index=allowed.get("human_pattern_label", ["unclear"]).index(
                sample.get("human_pattern_label", "unclear")
            ) if sample.get("human_pattern_label") in allowed.get("human_pattern_label", []) else 0
        )
        
        market_context = st.selectbox(
            "Market Context",
            allowed.get("market_context", ["unclear"]),
            index=allowed.get("market_context", ["unclear"]).index(
                sample.get("market_context", "unclear")
            ) if sample.get("market_context") in allowed.get("market_context", []) else 0
        )
        
        direction_context = st.selectbox(
            "Direction Context",
            allowed.get("direction_context", ["unclear"]),
            index=allowed.get("direction_context", ["unclear"]).index(
                sample.get("direction_context", "unclear")
            ) if sample.get("direction_context") in allowed.get("direction_context", []) else 0
        )
    
    with col2:
        structure_quality = st.slider("Structure Quality", 1, 5, int(sample.get("structure_quality", 3)))
        follow_through_quality = st.slider("Follow-through Quality", 1, 5, int(sample.get("follow_through_quality", 3)))
        review_confidence = st.slider("Review Confidence", 1, 5, int(sample.get("review_confidence", 3)))
    
    review_notes = st.text_area(
        "Review Notes",
        sanitize_optional_text_value(sample.get("review_notes", "")),
    )
    
    review_status = st.selectbox(
        "Review Status",
        allowed.get("review_status", ["pending", "reviewed"]),
        index=allowed.get("review_status", ["pending"]).index(
            sample.get("review_status", "pending")
        ) if sample.get("review_status") in allowed.get("review_status", []) else 0
    )
    
    # Save buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Save"):
            labels = {
                "human_pattern_label": human_pattern_label,
                "market_context": market_context,
                "direction_context": direction_context,
                "structure_quality": structure_quality,
                "follow_through_quality": follow_through_quality,
                "review_confidence": review_confidence,
                "review_notes": review_notes,
                "review_status": review_status
            }
            save_completed_review(batch, sample["sample_id"], labels, Path(completed_path))
            st.success("Saved!")
            st.rerun()
    
    with col2:
        if st.button("Save and Next"):
            labels = {
                "human_pattern_label": human_pattern_label,
                "market_context": market_context,
                "direction_context": direction_context,
                "structure_quality": structure_quality,
                "follow_through_quality": follow_through_quality,
                "review_confidence": review_confidence,
                "review_notes": review_notes,
                "review_status": review_status
            }
            save_completed_review(batch, sample["sample_id"], labels, Path(completed_path))
            if sample_idx < len(filtered) - 1:
                st.session_state.sample_idx = sample_idx + 1
            st.success("Saved!")
            st.rerun()
    
    with col3:
        if st.button("Reset Form"):
            st.rerun()


if __name__ == "__main__":
    main()
