from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent  # backend/


class Settings(BaseSettings):
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # Database
    db_path: str = str(BASE_DIR / "data" / "events.db")
    state_db_path: str = str(BASE_DIR / "data" / "state.db")

    # ChromaDB
    chroma_path: str = str(BASE_DIR / "data" / "memories")

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    default_model: str = "llama3.2:3b"

    # LLM
    llm_enabled: bool = True

    # Rewards
    rewards_dir: str = str(BASE_DIR.parent / "rewards" / "definitions")

    # Tick intervals (seconds)
    fast_tick_interval: int = 30
    slow_tick_interval: int = 300
    daily_tick_interval: int = 86400

    class Config:
        env_file = ".env"
        env_prefix = "SENTIA_"


settings = Settings()
