# Phase 7166–7285 — EURUSD 15m GUI Compact Review Layout

## Context

You are working in the Qlib Base / qlib-cajas repository.

Current workflow preference:

- The user now prefers working directly on `main`.
- Do not create a new feature branch unless the user explicitly asks.
- Work from local `main`.
- If remote sync is needed, use:
  - `git checkout main`
  - `git pull origin main`
- Do not perform automated merge operations.

Current GUI state:

- EURUSD 15m GUI review app is functional.
- K-line chart renders correctly.
- Chart diagnostics exist.
- `Review Notes` no longer displays `nan`.
- Streamlit width deprecation warning was addressed.
- GUI remains the human review interface.
- CSV/JSONL remain durable storage.

Current user problem:

- The GUI is too large/spacious.
- It requires too much vertical scrolling.
- The user wants a more compact layout so more of the review workflow fits on one screen.
- Current layout feels wide and tall:
  - large title
  - large chart area
  - metadata and form spread out
  - sliders and inputs consume too much vertical space
  - one-screen review is difficult

Project constraints:

- EURUSD 15m Bid only.
- No 1H/4H aggregation.
- No live trading.
- No paper trading.
- No broker routing.
- No order generation.
- No production model training.
- No Qlib core modifications.
- No labels invented by automation.
- GUI remains review interface.
- CSV/JSONL remain durable storage/interchange.

## Goal

Make the EURUSD 15m GUI review app more compact and suitable for high-frequency manual review.

This phase should:

1. Reduce vertical whitespace.
2. Reduce overly large headings/metrics.
3. Keep K-line chart readable but shorter.
4. Put candidate metadata and review controls into a tighter layout.
5. Make one-screen review more practical.
6. Preserve all existing save/update behavior and validation.
7. Keep default mode usable and optionally provide a compact mode toggle.

## Required Work

### 1. Inspect current GUI layout

Inspect:

```text
cajas/apps/eurusd_pattern_review_app.py
cajas/research/eurusd_pattern_review_gui.py
```

Identify layout blocks:

- page title
- sample metadata line
- chart title / chart container
- chart debug summary
- chart debug expander
- candidate metadata
- review labels section
- form controls
- save buttons
- sidebar configuration / filters / navigation / progress

### 2. Add compact page configuration and CSS

In the Streamlit app, add or refine:

```python
st.set_page_config(layout="wide", page_title="EURUSD 15m Review")
```

Add local CSS via `st.markdown(..., unsafe_allow_html=True)` to reduce excessive spacing.

Suggested CSS targets:

```css
.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
    max-width: 1500px;
}

h1, h2, h3 {
    margin-top: 0.25rem;
    margin-bottom: 0.5rem;
}

[data-testid="stMetricValue"] {
    font-size: 1.4rem;
}

[data-testid="stVerticalBlock"] {
    gap: 0.4rem;
}

.stTextInput, .stSelectbox, .stTextArea {
    margin-bottom: 0.25rem;
}
```

Be conservative. Do not make the UI unreadable.

### 3. Add Compact Mode toggle

Add a sidebar option:

```text
Compact mode: enabled by default
```

When compact mode is enabled:

- chart height should be smaller, e.g. `420` or configurable:
  - default compact chart height: `420`
  - normal chart height: `600`
- reduce title verbosity
- show metadata in one compact line
- use smaller chart diagnostics
- shorten the review form layout

When compact mode is disabled:

- preserve a more spacious layout close to the current behavior.

### 4. Compact chart section

Current chart takes a lot of vertical space.

In compact mode:

- chart height should be configurable in sidebar:
  - min 320
  - max 700
  - default 420
- keep width stretch
- keep target bar marker
- keep diagnostics visible
- diagnostics should be one line, e.g.

```text
Window 91 bars | traces 1 | exact match ✓ | fallback ✗ | target index 60
```

- keep detailed debug info inside expander, default collapsed.

### 5. Compact metadata layout

Currently candidate metadata is spread out.

Make it tighter:

- Use `st.columns` to place:
  - confidence score
  - review priority
  - reason codes
  - candidate type
- Use normal text or small metric values rather than huge metric blocks where appropriate.
- Avoid large vertical gaps.

Suggested compact display:

```text
sample_id=... | timestamp=... | type=compression_candidate | confidence=0.6889 | priority=low | reasons=...
```

### 6. Compact review form layout

The current form is too tall.

In compact mode:

- Put select boxes into columns:
  - Pattern Label / Market Context / Direction Context
- Put sliders into columns:
  - Structure Quality / Follow-through Quality / Review Confidence
- Put Review Status and buttons near the same visible area.
- Keep Review Notes text area shorter by default:
  - height around 70–90 px
  - placeholder: `Optional notes...`
- Buttons:
  - Save
  - Save and Next
  - Reset Form
  should be in one row.

Do not remove any fields.

### 7. Sidebar compacting

The sidebar is functional but tall.

Compact it slightly:

- keep path inputs
- keep Load/Reload
- keep filters
- keep sample index
- keep progress
- avoid large duplicated headings
- progress can be a compact line:
  - `Reviewed X / Total Y | Pending Z | Skipped W`

### 8. Preserve behavior

Do not change:

- completed CSV path
- duplicate-safe save by `sample_id`
- forbidden trading/action column sanitization
- label values
- review status values
- chart diagnostics logic
- readiness/report behavior

This is a layout/UX phase, not a data semantics phase.

### 9. Tests

Update:

```text
cajas/tests/test_eurusd_pattern_review_gui.py
```

If layout helper functions are introduced, test them.

Possible tests:

1. compact chart height config returns expected default.
2. notes sanitization remains stable.
3. completed CSV save/update still does not duplicate sample IDs.
4. forbidden trading columns still removed.
5. chart diagnostics summary formatting includes row count / trace count / exact/fallback flags.

Do not require launching Streamlit in tests.

### 10. Documentation

Update minimally:

```text
cajas/docs/eurusd_pattern_research_kickoff.md
cajas/README.md
tasks/eurusd_15m_research_end_to_end_roadmap.md
```

Document:

- compact mode exists
- compact mode is enabled by default
- chart height can be adjusted in the sidebar
- compact layout is intended for high-frequency manual review
- GUI remains review-only
- CSV/JSONL remain durable storage

### 11. Validation

Run focused tests:

```bash
./.venv-qlib313/bin/python -m pytest   cajas/tests/test_eurusd_pattern_review_gui.py   cajas/tests/test_validation_eurusd_pattern_review_gui.py
```

Run py_compile:

```bash
./.venv-qlib313/bin/python -m py_compile   cajas/apps/eurusd_pattern_review_app.py   cajas/research/eurusd_pattern_review_gui.py   cajas/tests/test_eurusd_pattern_review_gui.py
```

Run fast validation:

```bash
./.venv-qlib313/bin/python cajas/scripts/run_fast_validation.py --tier fast --timing-json tmp/fast_validation_latest.json
```

Run hygiene:

```bash
git diff --check
find cajas -path "*/init.py" -print
./.venv-qlib313/bin/python cajas/scripts/check_path_hygiene.py
```

### 12. Commit Guidance

Work directly on `main`.

Before editing:

```bash
git checkout main
git pull origin main
git status --short --branch
```

If clean, modify files directly on `main`.

Suggested commit:

```bash
git add   cajas/apps/eurusd_pattern_review_app.py   cajas/research/eurusd_pattern_review_gui.py   cajas/tests/test_eurusd_pattern_review_gui.py   cajas/docs/eurusd_pattern_research_kickoff.md   cajas/README.md   tasks/eurusd_15m_research_end_to_end_roadmap.md   tasks/phase_7166_7285_eurusd_15m_gui_compact_review_layout_prompt.md

git commit -m "fix: compact EURUSD GUI review layout"
```

Push directly to main only after validation:

```bash
git push origin main
```

Do not create a new branch unless explicitly requested.

Do not perform automated merge operations.

## Final Response Required

Report:

- active branch
- confirmation work was done on `main`
- commit created
- files changed
- compact mode status
- chart height default
- whether chart diagnostics remain visible
- whether review form fits more tightly
- whether save/update behavior is unchanged
- validation results
- fast validation runtime
- push status
- confirmation that GUI remains the review interface and CSV/JSONL remain durable storage
- confirmation that no labels were invented
- confirmation that no trading signals/orders/model training were produced
- confirmation that no automated merge was performed
