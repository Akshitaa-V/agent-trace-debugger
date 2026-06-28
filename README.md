# agent-trace-debugger

A local tool for tracing and debugging tool-using AI agents. I built this for a seminar on agentic AI, after running into the same problem the project ends up being about: when an agent's tool call succeeds and the final answer looks fine, you have basically no way of knowing whether it actually did the right thing.

## The problem this is solving

A tool-using agent can complete a task — no errors, valid-looking output — while still having silently done the wrong thing internally. Wrong tool arguments, ignored evidence, a final answer that violates a constraint from the original request. None of that shows up if you only look at whether execution succeeded. You have to look at the full trajectory, step by step, to catch it.

So I built something that does exactly that: logs every step an agent takes, then runs a set of rule-based checks against the trace to catch failures that are invisible if you only check "did it run."

## What's actually in here

- **agent.py** — the agent loop: classifies the query, picks a tool, builds the tool input, executes, records each step
- **tools.py** — a small mock tool layer (calculator, document retrieval, a structured hotel/restaurant search) — nothing external, no real APIs
- **tracer.py** — writes every step to a timestamped JSON trace, with a run ID, so any run is fully reproducible after the fact
- **debugger.py** — 5 rule-based checks run against each trace: price/constraint mismatches, tool errors, repeated calls, missing structured fields, unsupported queries
- **dashboard.py** — a Streamlit UI to run new queries, browse past traces, and see exactly what the debugger flagged and why

## Does it actually catch anything?

Yes — I tested it against 12 runs across 4 scenario types. 9 ran clean. The other 3 all executed without throwing any error and produced answers that looked reasonable on the surface, but the debugger correctly flagged all three: a hidden price-constraint violation, a missing required field that silently defaulted instead of failing loudly, and a query with no matching tool at all. That's the core point of the project — execution succeeding and the agent being *correct* are two different things, and you need the trace to tell them apart.

## How it compares to the tools people actually use for this

Part of the project was comparing this against LangSmith, Arize Phoenix, Weights & Biases Weave, and Langfuse — the real observability platforms teams use in production. They're all stronger on scale, dashboards, and ecosystem integration. What they're mostly missing, and what this prototype focuses on instead, is explicit decision-point violation detection: not just "here's the trace," but "here's specifically where and why this went wrong." That gap is what motivated building something rule-based and small enough to fully understand end to end, rather than reaching for a heavier platform.

## Running it

```bash
pip install -r requirements.txt
python main.py
```

Or to use the dashboard directly:

```bash
streamlit run dashboard.py
```

## Honest limitations

- Rule-based, not LLM-based — there's no real language model driving the agent's decisions here, which means it can't catch the kind of failures that only show up with genuine non-determinism
- Tools are mocked — no real external APIs or live data
- The rule engine is built around a fixed set of checks and won't generalize to constraint types it wasn't written for

## What I'd build next

Swapping the rule-based agent loop for a real LLM would be the obvious next step, specifically because it would surface the non-deterministic failure modes this version can't produce on its own. After that, I'd want to add semantic checks beyond keyword/structure matching — things like contradiction detection or grounding checks against retrieved evidence.
