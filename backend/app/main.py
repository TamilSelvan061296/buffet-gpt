import json
from contextlib import asynccontextmanager
from pathlib import Path

import yaml
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from .agent import build_agent
from .schemas import ChatRequest


CONFIG_PATH = Path(__file__).resolve().parent.parent / "ingestion_pipeline" / "config.yaml"
FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"


def load_config() -> dict:
    with CONFIG_PATH.open() as f:
        return yaml.safe_load(f)


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = load_config()
    async with AsyncSqliteSaver.from_conn_string(config["sessions"]["db_path"]) as saver:
        app.state.agent = build_agent(config, checkpointer=saver)
        yield


app = FastAPI(lifespan=lifespan)


def serialize_source(doc) -> dict:
    metadata = getattr(doc, "metadata", {}) or {}
    return {
        "year": metadata.get("year"),
        "source": metadata.get("source"),
        "start_index": metadata.get("start_index"),
        "content": getattr(doc, "page_content", ""),
    }


def serialize_tool_content(content) -> list[dict]:
    if not isinstance(content, str) or not content.strip():
        return []
    return [
        {
            "year": None,
            "source": None,
            "start_index": None,
            "content": block.strip(),
        }
        for block in content.split("\n\n")
        if block.strip()
    ]


def extract_usage(chunk) -> dict | None:
    usage = getattr(chunk, "usage_metadata", None)
    if not usage:
        usage = getattr(chunk, "response_metadata", {}).get("usage")
    if not usage:
        return None

    input_tokens = usage.get("input_tokens") or usage.get("prompt_tokens") or 0
    output_tokens = usage.get("output_tokens") or usage.get("completion_tokens") or 0
    total_tokens = usage.get("total_tokens") or input_tokens + output_tokens
    if not total_tokens:
        return None

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "estimated": False,
    }


def estimate_tokens(*texts: str) -> int:
    return max(1, sum(len(text or "") for text in texts) // 4)


def build_stats(req_message: str, response_text: str, sources: list[dict], usage: dict | None) -> dict:
    source_text = "\n\n".join(source.get("content", "") for source in sources)
    if usage:
        tokens = usage
    else:
        tokens = {
            "input_tokens": None,
            "output_tokens": None,
            "total_tokens": estimate_tokens(req_message, response_text, source_text),
            "estimated": True,
        }

    source_word_count = len(source_text.split())
    docs_referred = len(sources)
    reading_minutes = source_word_count / 220 if source_word_count else 0
    lookup_minutes = docs_referred * 1.5
    time_saved_minutes = round(reading_minutes + lookup_minutes)

    return {
        "tokens": tokens,
        "documents_referred": docs_referred,
        "approx_time_saved_minutes": time_saved_minutes,
        "time_saved_disclaimer": (
            "Approximate estimate based on retrieved context length, document count, "
            "and a 220 words-per-minute reading speed."
        ),
        "experimental": True,
    }


@app.post("/chat")
async def chat(req: ChatRequest):
    cfg = {"configurable": {"thread_id": req.session_id}}

    async def stream():
        response_parts: list[str] = []
        sources_for_response: list[dict] = []
        token_usage: dict | None = None

        async for chunk, _ in app.state.agent.astream(
            {"messages": [{"role": "user", "content": req.message}]},
            config=cfg,
            stream_mode="messages",
        ):
            print(f"chunk type {chunk.type}")
            print(chunk)
            
            if chunk.type == "tool":
                artifact = getattr(chunk, "artifact", None)
                if artifact:
                    sources = [serialize_source(doc) for doc in artifact]
                else:
                    sources = serialize_tool_content(chunk.content)
                if sources:
                    sources_for_response.extend(sources)
                    yield f"event: sources\ndata: {json.dumps(sources)}\n\n"
                continue

            usage = extract_usage(chunk)
            if usage and usage["total_tokens"] >= (token_usage or {}).get("total_tokens", 0):
                token_usage = usage

            text = ""
            if isinstance(chunk.content, str):
                text = chunk.content
            elif isinstance(chunk.content, list):
                for block in chunk.content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text += block.get("text", "")
            if text:
                response_parts.append(text)
                yield f"data: {json.dumps(text)}\n\n"
        stats = build_stats(
            req.message,
            "".join(response_parts),
            sources_for_response,
            token_usage,
        )
        yield f"event: stats\ndata: {json.dumps(stats)}\n\n"
        yield "event: end\ndata: \n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.get("/health")
def health():
    return {"ok": True}


# Serve the built React app at / in production. In dev, run Vite separately
# (`cd frontend && npm run dev`) — Vite's proxy forwards /chat and /health here.
if FRONTEND_DIST.exists():
    @app.get("/")
    async def root():
        return FileResponse(FRONTEND_DIST / "index.html")
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
