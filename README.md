# Multi-agent harness collaborator

A FastAPI wrapper around a LangGraph support workflow, plus a one-page UI that
shows which lane each question took through the graph. Prototype — runs locally,
not built for deployment.

A question enters the guardrail, gets routed by keyword to one of three agents,
and the reviewer produces the final answer. The UI draws that path and lists the
trace, so you can see the routing decision rather than infer it from the output.

## Layout

```
support-console/
├── app.py             # FastAPI app
├── graph.py           # your LangGraph definition
├── agents.py          # technical / billing / general / reviewer agents
├── requirements.txt
└── static/
    └── index.html     # the whole frontend, no build step
```

`static/` must sit next to `app.py`. The path is resolved as
`Path(__file__).parent / "static"`, so moving either one breaks the `/` route.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## One change needed in graph.py

The test call at the bottom of the file runs on import, which means it fires on
every uvicorn reload. Guard it:

```python
if __name__ == "__main__":
    print(run_workflow("Could you please tell me about the API issue 404"))
```

## Run

```bash
uvicorn app:app --reload --port 8080
```

Open http://127.0.0.1:8080

The pattern is `uvicorn <module>:<variable>` — module `app.py`, variable `app`.
Add `--host 0.0.0.0` to reach it from another device on your network.

To avoid retyping flags, run it from Python instead:

```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8080, reload=True)
```

Note the module string rather than the `app` object — reload needs the string form.

## Endpoints

| Method | Path          | Notes                                        |
|--------|---------------|----------------------------------------------|
| GET    | `/`           | The UI                                       |
| GET    | `/api/health` | Whether the graph imported cleanly           |
| POST   | `/api/ask`    | `{"question": "..."}` → route, answer, trace |
| GET    | `/docs`       | Swagger, from FastAPI                        |

Example:

```bash
curl -X POST http://127.0.0.1:8080/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Could you please tell me about the API issue 404"}'
```

```json
{
  "question": "Could you please tell me about the API issue 404",
  "route": "technical",
  "draft": "...",
  "final_answer": "...",
  "blocked": false,
  "trace": ["Guardrail has checked the request", "Router path:technical", "..."]
}
```

The backend imports `support_graph` directly rather than calling `run_workflow`,
because it also needs the `blocked` flag. A guardrail stop and a normal answer
both come back with a non-empty `final_answer`, so route alone can't tell them
apart.

## Known limits

This is a prototype. The guardrail is a hardcoded substring match rather than a
real safety layer, there's no auth or rate limiting on `/api/ask`, and CORS is
wide open. Fine for local work, none of it fine anywhere else.