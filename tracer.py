import json
import uuid
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
TRACE_DIR = BASE_DIR / "traces"
TRACE_DIR.mkdir(exist_ok=True)


def create_run_id() -> str:
    return f"run_{uuid.uuid4().hex[:8]}"


def create_trace(run_id: str, user_query: str) -> dict:
    return {
        "run_id": run_id,
        "user_query": user_query,
        "created_at": datetime.now().isoformat(),
        "steps": [],
        "final_answer": None,
        "detected_issues": []
    }


def add_step(
    trace: dict,
    step_id: int,
    event_type: str,
    agent_decision: str = None,
    tool_name: str = None,
    tool_input=None,
    tool_output=None,
    status: str = None,
    error_message: str = None
) -> None:
    step = {
        "step_id": step_id,
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "agent_decision": agent_decision,
        "tool_name": tool_name,
        "tool_input": tool_input,
        "tool_output": tool_output,
        "status": status,
        "error_message": error_message
    }

    trace["steps"].append(step)


def save_trace(trace: dict) -> str:
    file_path = TRACE_DIR / f"{trace['run_id']}.json"

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(trace, file, indent=4, ensure_ascii=False)

    return str(file_path)