from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent  # backend/


class Settings(BaseSettings):
    # Server
    host: str = "0.0.0.0"
    port: int = 7777
    debug: bool = True

    # Database
    db_path: str = str(BASE_DIR / "data" / "events.db")
    state_db_path: str = str(BASE_DIR / "data" / "state.db")

    # Memory
    memory_db_path: str = str(BASE_DIR / "data" / "memories.db")

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    default_model: str = "llama3.2:3b"

    # LLM
    llm_enabled: bool = True

    # Rewards
    rewards_dir: str = str(BASE_DIR.parent / "rewards" / "definitions")

    # Social / companion
    companion_name: str = "Vivek"

    # WhatsApp notifications
    whatsapp_provider: str = "callmebot"   # "callmebot" or "twilio"
    whatsapp_phone: str = ""               # CallMeBot: phone with country code, no +  e.g. 447700900000
    whatsapp_api_key: str = ""             # CallMeBot API key (from activation message)
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from: str = "whatsapp:+14155238886"   # Twilio sandbox number
    twilio_to: str = ""                          # your WhatsApp number: whatsapp:+44...

    # Tick intervals (seconds)
    fast_tick_interval: int = 30
    slow_tick_interval: int = 300
    daily_tick_interval: int = 86400

    class Config:
        env_file = ".env"
        env_prefix = "SENTIA_"


settings = Settings()
