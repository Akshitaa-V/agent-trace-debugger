import re

from tools import (
    calculator_tool,
    document_retrieval_tool,
    structured_search_tool
)

from tracer import (
    create_run_id,
    create_trace,
    add_step,
    save_trace
)

from debugger import run_debugging_checks


def is_computation_query(query: str) -> bool:
    math_keywords = ["calculate", "what is", "compute"]
    has_operator = any(op in query for op in ["+", "-", "*", "/", "×"])

    return any(keyword in query.lower() for keyword in math_keywords) and has_operator


def extract_math_expression(query: str) -> str:
    expression = query.lower()
    expression = expression.replace("what is", "")
    expression = expression.replace("calculate", "")
    expression = expression.replace("compute", "")
    expression = expression.replace("?", "")
    expression = expression.replace("×", "*")
    return expression.strip()


def is_document_query(query: str) -> bool:
    document_keywords = [
        "document",
        "monitoring",
        "tracing",
        "observability",
        "debugging",
        "agent failures"
    ]

    return any(keyword in query.lower() for keyword in document_keywords)


def is_structured_search_query(query: str) -> bool:
    search_keywords = ["hotel", "restaurant", "flight", "under"]

    return any(keyword in query.lower() for keyword in search_keywords)


def extract_structured_input(query: str) -> dict:
    query_lower = query.lower()

    category = "hotel"
    if "restaurant" in query_lower:
        category = "restaurant"
    elif "flight" in query_lower:
        category = "flight"

    city = "Unknown"
    known_cities = ["munich", "berlin", "passau", "paris"]

    for known_city in known_cities:
        if known_city in query_lower:
            city = known_city.capitalize()

    price_match = re.search(r"under\s*€?\s*(\d+)", query_lower)

    if price_match:
        max_price = int(price_match.group(1))
    else:
        max_price = 9999

    return {
        "category": category,
        "city": city,
        "max_price": max_price
    }


def analyze_query_type(user_query: str) -> str:
    if is_computation_query(user_query):
        return "computation"
    if is_structured_search_query(user_query):
        return "structured_search"
    if is_document_query(user_query):
        return "document_retrieval"
    return "unknown"


def run_agent(user_query: str, simulate_failure: bool = False) -> dict:
    run_id = create_run_id()
    trace = create_trace(run_id, user_query)

    step_id = 1

    # Step 1: user query received
    add_step(
        trace=trace,
        step_id=step_id,
        event_type="user_query",
        agent_decision="received_user_query",
        tool_name=None,
        tool_input=None,
        tool_output=user_query,
        status="success"
    )

    step_id += 1

    # Step 2: query analysis
    query_type = analyze_query_type(user_query)

    add_step(
        trace=trace,
        step_id=step_id,
        event_type="query_analysis",
        agent_decision=f"classified_query_as_{query_type}",
        tool_name=None,
        tool_input=user_query,
        tool_output={"query_type": query_type},
        status="success"
    )

    step_id += 1

    # Unknown query case
    if query_type == "unknown":
        add_step(
            trace=trace,
            step_id=step_id,
            event_type="tool_selection",
            agent_decision="no_suitable_tool_found",
            tool_name=None,
            tool_input=None,
            tool_output=None,
            status="success"
        )

        step_id += 1

        trace["final_answer"] = "No suitable tool was found for this query."

        add_step(
            trace=trace,
            step_id=step_id,
            event_type="final_answer_generation",
            agent_decision="generate_fallback_answer",
            tool_name=None,
            tool_input=None,
            tool_output=trace["final_answer"],
            status="success"
        )

        step_id += 1

        issues = run_debugging_checks(trace)
        trace["detected_issues"] = issues

        add_step(
            trace=trace,
            step_id=step_id,
            event_type="debugging_check",
            agent_decision="run_debugging_rules",
            tool_name=None,
            tool_input=None,
            tool_output=issues,
            status="success"
        )

        save_trace(trace)
        return trace

    # Step 3: tool selection
    if query_type == "computation":
        selected_tool = "calculator_tool"
        agent_decision = "select_computation_tool"

    elif query_type == "document_retrieval":
        selected_tool = "document_retrieval_tool"
        agent_decision = "select_document_retrieval_tool"

    else:
        selected_tool = "structured_search_tool"
        agent_decision = "select_structured_search_tool"

    add_step(
        trace=trace,
        step_id=step_id,
        event_type="tool_selection",
        agent_decision=agent_decision,
        tool_name=selected_tool,
        tool_input={"query_type": query_type},
        tool_output={"selected_tool": selected_tool},
        status="success"
    )

    step_id += 1

    # Step 4: tool input generation
    if query_type == "computation":
        tool_input = extract_math_expression(user_query)

    elif query_type == "document_retrieval":
        tool_input = user_query

    else:
        tool_input = extract_structured_input(user_query)

        # Used only to demonstrate a failure case.
        if simulate_failure and tool_input["max_price"] == 120:
            tool_input["max_price"] = 200

    add_step(
        trace=trace,
        step_id=step_id,
        event_type="tool_input_generation",
        agent_decision="generate_tool_input",
        tool_name=selected_tool,
        tool_input=user_query,
        tool_output=tool_input,
        status="success"
    )

    step_id += 1

    # Step 5: tool execution
    if query_type == "computation":
        result = calculator_tool(tool_input)

    elif query_type == "document_retrieval":
        result = document_retrieval_tool(tool_input)

    else:
        result = structured_search_tool(
            category=tool_input["category"],
            city=tool_input["city"],
            max_price=tool_input["max_price"]
        )

    add_step(
        trace=trace,
        step_id=step_id,
        event_type="tool_call",
        agent_decision=f"execute_{query_type}",
        tool_name=selected_tool,
        tool_input=tool_input,
        tool_output=result["output"],
        status=result["status"],
        error_message=result["error"]
    )

    step_id += 1

    # Step 6: tool output observation
    add_step(
        trace=trace,
        step_id=step_id,
        event_type="tool_output_observation",
        agent_decision="observe_tool_result",
        tool_name=selected_tool,
        tool_input=None,
        tool_output=result,
        status=result["status"],
        error_message=result["error"]
    )

    step_id += 1

    # Step 7: final answer generation
    if query_type == "computation":
        if result["status"] == "success":
            trace["final_answer"] = f"The answer is {result['output']}."
        else:
            trace["final_answer"] = "The computation failed."

    elif query_type == "document_retrieval":
        if result["status"] == "success":
            doc = result["output"]
            trace["final_answer"] = (
                f"According to {doc['title']}: {doc['content']}"
            )
        else:
            trace["final_answer"] = "No relevant document was found."

    else:
        if result["status"] == "success" and result["output"]:
            item = result["output"][0]
            trace["final_answer"] = (
                f"{item['name']} is available in {item['city']} "
                f"for €{item['price']}."
            )
        elif result["status"] == "success":
            trace["final_answer"] = "No matching result found."
        else:
            trace["final_answer"] = "The structured search failed."

    add_step(
        trace=trace,
        step_id=step_id,
        event_type="final_answer_generation",
        agent_decision="generate_final_answer",
        tool_name=None,
        tool_input=result["output"],
        tool_output=trace["final_answer"],
        status="success"
    )

    step_id += 1

    # Step 8: debugging checks
    issues = run_debugging_checks(trace)
    trace["detected_issues"] = issues

    add_step(
        trace=trace,
        step_id=step_id,
        event_type="debugging_check",
        agent_decision="run_debugging_rules",
        tool_name=None,
        tool_input=None,
        tool_output=issues,
        status="success"
    )

    save_trace(trace)

    return trace