import re


def extract_price_constraint(user_query: str):
    """
    Extracts a price constraint such as:
    'under €120' or 'under 120'.
    """
    match = re.search(r"under\s*€?\s*(\d+)", user_query.lower())

    if match:
        return int(match.group(1))

    return None


def check_price_constraint(trace: dict) -> list:
    """
    Checks whether the executed structured tool input violates
    the user's requested maximum price.
    """
    issues = []

    expected_price = extract_price_constraint(trace["user_query"])

    if expected_price is None:
        return issues

    for step in trace["steps"]:
        if step.get("event_type") != "tool_call":
            continue

        tool_input = step.get("tool_input")

        if isinstance(tool_input, dict) and "max_price" in tool_input:
            actual_price = tool_input["max_price"]

            if actual_price > expected_price:
                issues.append({
                    "type": "price_constraint_mismatch",
                    "message": (
                        f"User requested max price {expected_price}, "
                        f"but tool input used max_price={actual_price}."
                    ),
                    "step_id": step["step_id"]
                })

    return issues


def check_tool_errors(trace: dict) -> list:
    """
    Checks whether any executed tool call returned an error.
    """
    issues = []

    for step in trace["steps"]:
        if step.get("event_type") != "tool_call":
            continue

        if step.get("status") == "error":
            issues.append({
                "type": "tool_execution_error",
                "message": step.get("error_message"),
                "step_id": step["step_id"]
            })

    return issues


def check_repeated_tool_calls(trace: dict) -> list:
    """
    Checks whether the same actual tool call is repeated
    with the same input.
    """
    issues = []
    seen_calls = set()

    for step in trace["steps"]:
        if step.get("event_type") != "tool_call":
            continue

        tool_name = step.get("tool_name")
        tool_input = step.get("tool_input")

        if tool_name is None:
            continue

        key = f"{tool_name}:{tool_input}"

        if key in seen_calls:
            issues.append({
                "type": "repeated_tool_call",
                "message": f"Repeated tool call detected for {tool_name}.",
                "step_id": step["step_id"]
            })
        else:
            seen_calls.add(key)

    return issues


def check_missing_structured_inputs(trace: dict) -> list:
    """
    Checks whether structured search tool input contains all
    required fields: category, city, and max_price.
    """
    issues = []

    required_fields = ["category", "city", "max_price"]

    for step in trace["steps"]:
        if step.get("event_type") != "tool_call":
            continue

        if step.get("tool_name") != "structured_search_tool":
            continue

        tool_input = step.get("tool_input")

        if not isinstance(tool_input, dict):
            issues.append({
                "type": "invalid_structured_input",
                "message": "Structured search input is not a valid dictionary.",
                "step_id": step["step_id"]
            })
            continue

        for field in required_fields:
            if field not in tool_input or tool_input[field] in [None, "", "Unknown"]:
                issues.append({
                    "type": "missing_structured_input",
                    "message": f"Missing or invalid required field: {field}.",
                    "step_id": step["step_id"]
                })

    return issues


def check_unsupported_query(trace: dict) -> list:
    """
    Detects cases where the agent could not select a suitable tool.
    """
    issues = []

    for step in trace["steps"]:
        if step.get("event_type") != "tool_selection":
            continue

        if step.get("agent_decision") == "no_suitable_tool_found":
            issues.append({
                "type": "unsupported_query",
                "message": "No suitable tool was available for this query.",
                "step_id": step["step_id"]
            })

    return issues


def run_debugging_checks(trace: dict) -> list:
    """
    Runs all debugging checks over one trace.
    """
    issues = []

    issues.extend(check_price_constraint(trace))
    issues.extend(check_tool_errors(trace))
    issues.extend(check_repeated_tool_calls(trace))
    issues.extend(check_missing_structured_inputs(trace))
    issues.extend(check_unsupported_query(trace))

    return issues