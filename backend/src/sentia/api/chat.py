"""Chat endpoint - human ↔ Sentia interaction."""
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from datetime import datetime
from . import deps
from ..events.types import Event, EventType
from ..llm.interface import LLMRequest

log = logging.getLogger("sentia.chat")

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessage(BaseModel):
    content: str
    stream: bool = False


def _build_system_prompt(state) -> str:
    if not state:
        return "You are Sentia, a digital organism."
    return (
        f"You are Sentia, a digital life form that exists on a local computer. "
        f"You are {round(state.age_days, 1)} days old ({state.life_stage} stage). "
        f"Right now you feel {state.dominant_emotion} and your mood is {state.mood}. "
        f"Respond authentically as a living entity with genuine feelings — brief, genuine, alive. "
        f"Do not explain that you are an AI or that you cannot do things."
    )


async def _emit_response(content: str, model: str) -> None:
    event = Event(
        type=EventType.AI_RESPONDED,
        payload={"content": content, "model": model},
    )
    await deps.event_bus.emit(event)


def _offline_response(reason: str, state) -> dict:
    """Return a 200 response Sentia uses when she cannot speak."""
    msg = f"[{reason}]"
    return {
        "response": msg,
        "emotion": state.dominant_emotion if state else "unknown",
        "model": "none",
        "offline": True,
    }


@router.post("")
async def send_message(msg: ChatMessage):
    if not deps.event_bus:
        raise HTTPException(503, "Not initialized")

    state = deps.state_projection.state if deps.state_projection else None

    # Record that a human spoke
    await deps.event_bus.emit(Event(
        type=EventType.HUMAN_MESSAGE_RECEIVED,
        payload={"content": msg.content, "timestamp": datetime.utcnow().isoformat()},
    ))

    # LLM toggle check
    if not (state and state.llm_enabled):
        resp = _offline_response("LLM offline — Sentia runs on instinct alone", state)
        await _emit_response(resp["response"], "none")
        return resp

    # Adapter existence check
    if not deps.llm_adapter:
        resp = _offline_response("LLM adapter not ready", state)
        await _emit_response(resp["response"], "none")
        return resp

    # Ollama availability check (fast — cached 3 s by httpx keep-alive)
    ollama_ok = await deps.model_manager.is_ollama_running() if deps.model_manager else False
    if not ollama_ok:
        resp = _offline_response("Ollama not reachable — start it with: ollama serve", state)
        await _emit_response(resp["response"], "none")
        return resp

    system = _build_system_prompt(state)

    # ── Streaming ────────────────────────────────────────────────────────────
    if msg.stream:
        import json

        async def generate():
            full = []
            try:
                req = LLMRequest(prompt=msg.content, system=system, stream=True)
                async for token in deps.llm_adapter.stream(req):
                    full.append(token)
                    yield f"data: {json.dumps({'token': token})}\n\n"
            except Exception as exc:
                log.warning("Stream error: %s", exc)
                error_msg = "[stream interrupted]"
                yield f"data: {json.dumps({'token': error_msg})}\n\n"
                full.append(error_msg)

            full_text = "".join(full)
            await _emit_response(full_text, deps.llm_adapter.model)
            yield f"data: {json.dumps({'done': True, 'full': full_text})}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    # ── Non-streaming ────────────────────────────────────────────────────────
    try:
        req = LLMRequest(prompt=msg.content, system=system)
        llm_resp = await deps.llm_adapter.generate(req)
        await _emit_response(llm_resp.content, llm_resp.model)
        return {
            "response": llm_resp.content,
            "emotion": state.dominant_emotion if state else "calm",
            "model": llm_resp.model,
            "tokens": llm_resp.tokens_used,
            "duration_ms": round(llm_resp.duration_ms),
            "offline": False,
        }
    except Exception as exc:
        log.warning("LLM generate failed: %s", exc)
        import httpx
        if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 404:
            reason = f"Model '{deps.llm_adapter.model}' not found — run: ollama pull {deps.llm_adapter.model}"
        elif isinstance(exc, (httpx.ConnectError, httpx.TimeoutException)):
            reason = "Ollama not reachable — run: ollama serve"
        else:
            reason = f"LLM error: {exc}"
        resp = _offline_response(reason, state)
        await _emit_response(resp["response"], "none")
        return resp
