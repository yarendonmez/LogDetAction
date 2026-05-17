import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[1] / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Model paths
    CLASSIFIER_ADAPTER_PATH: str = r"C:\developer\LogDetAction\v2.0\qlora_classifier_test_model"
    ANALYSIS_ADAPTER_PATH: str = r"C:\developer\LogDetAction\v2.0\qlora_test_model"
    BASE_MODEL_ID: str = "mistralai/Mistral-7B-Instruct-v0.2"

    # Runtime
    DEVICE: str = "cuda"
    MAX_NEW_TOKENS_CLASSIFICATION: int = 20
    MAX_NEW_TOKENS_ANALYSIS: int = 300
    DEFAULT_ANALYSIS_MODE: str = "combined"

    # Storage — paths relative to project root
    RESULTS_DIR: str = "backend/results/pipeline"
    UPLOADS_DIR: str = "backend/uploads"
    DB_PATH: str = "backend/logdetaction.db"

    # Live monitor
    LIVE_LOG_PATH: str = "backend/live/live_demo.log"
    LIVE_POLL_INTERVAL_SEC: float = 2.0
    LIVE_DEFAULT_ANALYSIS_MODE: str = "combined"

    # Server
    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000

    @property
    def results_dir_abs(self) -> Path:
        base = Path(__file__).resolve().parents[1]
        return base / self.RESULTS_DIR

    @property
    def uploads_dir_abs(self) -> Path:
        base = Path(__file__).resolve().parents[1]
        return base / self.UPLOADS_DIR

    @property
    def live_log_path_abs(self) -> Path:
        base = Path(__file__).resolve().parents[1]
        return base / self.LIVE_LOG_PATH

    @property
    def db_url(self) -> str:
        base = Path(__file__).resolve().parents[1]
        db_path = base / self.DB_PATH
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite+aiosqlite:///{db_path}"


settings = Settings()

# Ensure runtime directories exist
settings.results_dir_abs.mkdir(parents=True, exist_ok=True)
settings.uploads_dir_abs.mkdir(parents=True, exist_ok=True)
settings.live_log_path_abs.parent.mkdir(parents=True, exist_ok=True)
