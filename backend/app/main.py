import json
from contextlib import asynccontextmanager
from pathlib import Path

import yaml
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
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


@app.post("/chat")
async def chat(req: ChatRequest):
    cfg = {"configurable": {"thread_id": req.session_id}}

    async def stream():
        async for chunk, _ in app.state.agent.astream(
            {"messages": [{"role": "user", "content": req.message}]},
            config=cfg,
            stream_mode="messages",
        ):
            print(f"chunk type {chunk.type}")
            print(chunk)
            
            if chunk.type == "tool":
                continue
            text = ""
            if isinstance(chunk.content, str):
                text = chunk.content
            elif isinstance(chunk.content, list):
                for block in chunk.content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text += block.get("text", "")
            if text:
                yield f"data: {json.dumps(text)}\n\n"
        yield "event: end\ndata: \n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.get("/health")
def health():
    return {"ok": True}


# Serve the built React app at / in production. In dev, run Vite separately
# (`cd frontend && npm run dev`) — Vite's proxy forwards /chat and /health here.
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
