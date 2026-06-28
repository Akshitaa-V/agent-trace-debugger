import json
from pathlib import Path

import streamlit as st

from agent import run_agent


TRACE_DIR = Path(__file__).resolve().parent / "traces"


def load_trace(file_path: Path) -> dict:
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def display_value(value):
    if isinstance(value, (dict, list)):
        st.json(value)
    elif value is None:
        st.write("None")
    else:
        st.code(str(value))


def get_trace_status(trace: dict) -> str:
    issues = trace.get("detected_issues", [])
    if issues:
        return "Failed"
    return "Success"


st.set_page_config(
    page_title="Agent Trace Debugger",
    layout="wide"
)

st.title("Agent Trace Debugger")
st.write("Trace-based observability prototype for tool-using AI agents.")


# ------------------------------------------------------------
# Sidebar Section 1: Run a New Query
# ------------------------------------------------------------
st.sidebar.header("Run New Agent Query")

with st.sidebar.form("new_query_form"):
    new_query = st.text_area(
        "Enter a user query",
        placeholder="Example: Find a hotel in Munich under €120."
    )

    simulate_failure = st.checkbox(
        "Simulate structured-input failure"
    )

    submitted = st.form_submit_button("Run Agent")

if submitted:
    cleaned_query = new_query.strip()

    if not cleaned_query:
        st.sidebar.error("Please enter a query before running the agent.")
    else:
        run_agent(
            cleaned_query,
            simulate_failure=simulate_failure
        )

        st.sidebar.success("New trace generated successfully.")
        st.rerun()


# ------------------------------------------------------------
# Load Existing Traces
# ------------------------------------------------------------
trace_files = sorted(
    TRACE_DIR.glob("*.json"),
    key=lambda path: path.stat().st_mtime,
    reverse=True
)

if not trace_files:
    st.warning("No traces found. Run a new query from the sidebar.")
else:
    traces = []

    for file_path in trace_files:
        trace = load_trace(file_path)
        trace["_file_name"] = file_path.name
        trace["_status"] = get_trace_status(trace)
        traces.append(trace)

    total_runs = len(traces)
    failed_runs = sum(1 for trace in traces if trace["_status"] == "Failed")
    successful_runs = total_runs - failed_runs

    # ------------------------------------------------------------
    # Dashboard Summary
    # ------------------------------------------------------------
    st.header("Dashboard Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Runs", total_runs)

    with col2:
        st.metric("Successful Runs", successful_runs)

    with col3:
        st.metric("Failed Runs", failed_runs)

    # ------------------------------------------------------------
    # Sidebar Section 2: Trace Selection
    # ------------------------------------------------------------
    st.sidebar.header("Trace Selection")

    filter_option = st.sidebar.radio(
        "Filter runs",
        ["All", "Success", "Failed"]
    )

    if filter_option == "All":
        filtered_traces = traces
    else:
        filtered_traces = [
            trace for trace in traces
            if trace["_status"] == filter_option
        ]

    if not filtered_traces:
        st.warning(f"No {filter_option.lower()} traces found.")
    else:
        selected_trace_name = st.sidebar.selectbox(
            "Select a trace run",
            [trace["_file_name"] for trace in filtered_traces]
        )

        trace = next(
            trace for trace in filtered_traces
            if trace["_file_name"] == selected_trace_name
        )

        # ------------------------------------------------------------
        # Run Overview
        # ------------------------------------------------------------
        st.header("Run Overview")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("Run ID")
            st.write(trace.get("run_id"))

        with col2:
            st.subheader("Status")
            if trace["_status"] == "Failed":
                st.error("Failed")
            else:
                st.success("Success")

        with col3:
            st.subheader("Steps")
            st.write(len(trace.get("steps", [])))

        st.subheader("User Query")
        st.write(trace.get("user_query"))

        st.subheader("Final Answer")
        st.write(trace.get("final_answer"))

        # ------------------------------------------------------------
        # Detected Issues
        # ------------------------------------------------------------
        st.header("Detected Issues")

        issues = trace.get("detected_issues", [])

        if issues:
            for issue in issues:
                st.error(
                    f"{issue.get('type')} at step {issue.get('step_id')}: "
                    f"{issue.get('message')}"
                )
        else:
            st.success("No issues detected.")

        # ------------------------------------------------------------
        # Step Summary Table
        # ------------------------------------------------------------
        st.header("Step Summary")

        issue_steps = {
            issue.get("step_id")
            for issue in trace.get("detected_issues", [])
        }

        step_rows = []

        for step in trace.get("steps", []):
            step_id = step.get("step_id")

            if step_id in issue_steps:
                debug_status = "issue_detected"
            else:
                debug_status = "no_issue"

            step_rows.append({
                "step_id": step_id,
                "event_type": step.get("event_type"),
                "agent_decision": step.get("agent_decision"),
                "tool_name": step.get("tool_name"),
                "execution_status": step.get("status"),
                "debug_status": debug_status
            })

        st.dataframe(step_rows, use_container_width=True)

        # ------------------------------------------------------------
        # Detailed Step-by-Step Trace
        # ------------------------------------------------------------
        st.header("Step-by-Step Trace")

        for step in trace.get("steps", []):
            title = f"Step {step.get('step_id')} — {step.get('event_type')}"

            with st.expander(title, expanded=False):
                st.write("**Timestamp:**", step.get("timestamp"))
                st.write("**Agent Decision:**", step.get("agent_decision"))
                st.write("**Tool Name:**", step.get("tool_name"))

                st.write("**Tool Input:**")
                display_value(step.get("tool_input"))

                st.write("**Tool Output:**")
                display_value(step.get("tool_output"))

                st.write("**Execution Status:**", step.get("status"))
                st.write("**Error Message:**", step.get("error_message"))

        # ------------------------------------------------------------
        # Raw JSON Trace
        # ------------------------------------------------------------
        st.header("Raw Trace JSON")
        st.json(trace)