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


def run_agent(user_query: str, simulate_failure: bool = False) -> dict:
    run_id = create_run_id()
    trace = create_trace(run_id, user_query)

    step_id = 1

    add_step(
        trace=trace,
        step_id=step_id,
        event_type="user_query",
        agent_decision="received_user_query",
        status="success"
    )

    step_id += 1

    if is_computation_query(user_query):
        expression = extract_math_expression(user_query)

        add_step(
            trace=trace,
            step_id=step_id,
            event_type="agent_decision",
            agent_decision="select_computation_tool",
            tool_name="calculator_tool",
            tool_input=expression,
            status="success"
        )

        step_id += 1

        result = calculator_tool(expression)

        add_step(
            trace=trace,
            step_id=step_id,
            event_type="tool_call",
            agent_decision="execute_computation",
            tool_name="calculator_tool",
            tool_input=expression,
            tool_output=result["output"],
            status=result["status"],
            error_message=result["error"]
        )

        if result["status"] == "success":
            trace["final_answer"] = f"The answer is {result['output']}."
        else:
            trace["final_answer"] = "The computation failed."

    elif is_structured_search_query(user_query):
        structured_input = extract_structured_input(user_query)

        # This intentionally creates a failure for demonstration.
        if simulate_failure and structured_input["max_price"] == 120:
            structured_input["max_price"] = 200

        add_step(
            trace=trace,
            step_id=step_id,
            event_type="agent_decision",
            agent_decision="select_structured_search_tool",
            tool_name="structured_search_tool",
            tool_input=structured_input,
            status="success"
        )

        step_id += 1

        result = structured_search_tool(
            category=structured_input["category"],
            city=structured_input["city"],
            max_price=structured_input["max_price"]
        )

        add_step(
            trace=trace,
            step_id=step_id,
            event_type="tool_call",
            agent_decision="execute_structured_search",
            tool_name="structured_search_tool",
            tool_input=structured_input,
            tool_output=result["output"],
            status=result["status"],
            error_message=result["error"]
        )

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

    elif is_document_query(user_query):
        retrieval_query = user_query

        add_step(
            trace=trace,
            step_id=step_id,
            event_type="agent_decision",
            agent_decision="select_document_retrieval_tool",
            tool_name="document_retrieval_tool",
            tool_input=retrieval_query,
            status="success"
        )

        step_id += 1

        result = document_retrieval_tool(retrieval_query)

        add_step(
            trace=trace,
            step_id=step_id,
            event_type="tool_call",
            agent_decision="execute_document_retrieval",
            tool_name="document_retrieval_tool",
            tool_input=retrieval_query,
            tool_output=result["output"],
            status=result["status"],
            error_message=result["error"]
        )

        if result["status"] == "success":
            doc = result["output"]
            trace["final_answer"] = (
                f"According to {doc['title']}: {doc['content']}"
            )
        else:
            trace["final_answer"] = "No relevant document was found."

    else:
        add_step(
            trace=trace,
            step_id=step_id,
            event_type="agent_decision",
            agent_decision="no_tool_selected",
            status="success"
        )

        trace["final_answer"] = "No suitable tool was found for this query."

    issues = run_debugging_checks(trace)
    trace["detected_issues"] = issues

    save_trace(trace)

    return trace