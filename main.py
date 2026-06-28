from agent import run_agent


def print_trace_summary(trace: dict):
    print("\n==============================")
    print(f"Run ID: {trace['run_id']}")
    print(f"User Query: {trace['user_query']}")
    print(f"Final Answer: {trace['final_answer']}")

    print("\nSteps:")
    for step in trace["steps"]:
        print(f"- Step {step['step_id']}: {step['event_type']}")
        print(f"  Decision: {step.get('agent_decision')}")
        print(f"  Tool: {step.get('tool_name')}")
        print(f"  Input: {step.get('tool_input')}")
        print(f"  Output: {step.get('tool_output')}")
        print(f"  Status: {step.get('status')}")

    print("\nDetected Issues:")
    if trace["detected_issues"]:
        for issue in trace["detected_issues"]:
            print(f"- {issue['type']}: {issue['message']}")
    else:
        print("- None")

    print("==============================\n")


if __name__ == "__main__":
    test_queries = [
        # Computation scenarios
        ("What is 25 * 8?", False),
        ("Calculate 2 + 2.", False),
        ("What is (12 + 8) * 3?", False),

        # Document retrieval scenarios
        ("What does the document say about monitoring?", False),
        ("What does the document say about tracing?", False),
        ("What does the document say about debugging?", False),

        # Structured search success scenarios
        ("Find a hotel in Munich under €120.", False),
        ("Find a restaurant in Passau under €30.", False),
        ("Find a hotel in Berlin under €100.", False),

        # Structured search failure: missing city
        ("Find a hotel under €120.", False),

        # Structured search failure: violated price constraint
        ("Find a hotel in Munich under €120.", True),

        # Unsupported query failure
        ("Tell me a joke.", False)
    ]

    for query, simulate_failure in test_queries:
        trace = run_agent(query, simulate_failure=simulate_failure)
        print_trace_summary(trace)