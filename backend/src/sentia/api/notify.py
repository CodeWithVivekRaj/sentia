"""Notification API — test and inspect WhatsApp configuration."""
from fastapi import APIRouter
from . import deps

router = APIRouter(prefix="/notify", tags=["notify"])


@router.get("/status")
async def notify_status():
    wa = deps.whatsapp
    if not wa:
        return {"whatsapp": {"configured": False, "provider": None}}
    return {
        "whatsapp": {
            "configured": wa.enabled,
            "provider": wa.provider,
        }
    }


@router.post("/test")
async def send_test():
    wa = deps.whatsapp
    if not wa:
        return {"ok": False, "error": "WhatsApp notifier not initialised"}
    if not wa.enabled:
        return {
            "ok": False,
            "error": (
                "WhatsApp not configured. "
                "Set SENTIA_WHATSAPP_PHONE and SENTIA_WHATSAPP_API_KEY in your .env file."
            ),
        }
    state = deps.state_projection.state if deps.state_projection else None
    emotion = state.dominant_emotion if state else "calm"
    sent = await wa.send(f"Sentia ({emotion}): Test message — I can reach you here.")
    return {"ok": sent}
