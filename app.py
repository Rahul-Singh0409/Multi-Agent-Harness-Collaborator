"""
FastAPI backend for the LangGraph support workflow.

Run:
    uvicorn main:app --reload

Expects graph.py (your file) to sit next to this one and expose run_workflow().
"""

from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

STATIC_DIR = Path(__file__).parent / "static"

# Import the graph lazily and remember why it failed, so the UI can show a
# useful message instead of the server refusing to start.
GRAPH_IMPORT_ERROR: str | None = None
support_graph = None

try:
    from graph import SupportState, support_graph  # type: ignore
except Exception as exc:  # noqa: BLE001 - we want to surface any import problem
    GRAPH_IMPORT_ERROR = f"{type(exc).__name__}: {exc}"


app = FastAPI(title="Support workflow console")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this before you deploy anywhere real
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class AskResponse(BaseModel):
    question: str
    route: str
    draft: str
    final_answer: str
    blocked: bool
    trace: list[str]


def build_initial_state(question: str) -> dict[str, Any]:
    return {
        "question": question,
        "route": "",
        "draft": "",
        "final_answer": "",
        "blocked": False,
        "trace": [],
    }


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "graph_loaded": support_graph is not None,
        "error": GRAPH_IMPORT_ERROR,
    }


@app.post("/api/ask", response_model=AskResponse)
def ask(payload: AskRequest) -> Any:
    if support_graph is None:
        return JSONResponse(
            status_code=503,
            content={
                "detail": "The graph could not be imported.",
                "error": GRAPH_IMPORT_ERROR,
                "hint": (
                    "Check that graph.py and agents.py are next to main.py, and that "
                    "graph.py has no module-level run_workflow() call — wrap it in "
                    "if __name__ == '__main__':"
                ),
            },
        )

    question = payload.question.strip()
    result = support_graph.invoke(build_initial_state(question))

    blocked = bool(result.get("blocked", False))

    return AskResponse(
        question=question,
        route=result.get("route") or ("blocked" if blocked else "unknown"),
        draft=result.get("draft", ""),
        final_answer=result.get("final_answer", ""),
        blocked=blocked,
        trace=result.get("trace", []),
    )


# Serve the frontend from the same origin, so there is no CORS story in dev.
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")