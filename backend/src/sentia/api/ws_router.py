"""WebSocket endpoint - real-time event stream to clients."""
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from . import deps

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    if not deps.ws_manager:
        await ws.close(code=1011)
        return

    await deps.ws_manager.connect(ws)

    # Send current state on connect
    if deps.state_projection:
        await deps.ws_manager.send_to(ws, {
            "type": "state_snapshot",
            "data": deps.state_projection.snapshot(),
        })

    try:
        while True:
            # Keep alive - client can send pings
            data = await ws.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await deps.ws_manager.send_to(ws, {"type": "pong"})
            except Exception:
                pass
    except WebSocketDisconnect:
        deps.ws_manager.disconnect(ws)
