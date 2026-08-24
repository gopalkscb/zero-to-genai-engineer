"""Application configuration via pydantic-settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/ root — parent of app/
BACKEND_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_ROOT.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Repo-root .env (where .env.example lives) then backend/.env override
        env_file=(str(REPO_ROOT / ".env"), str(BACKEND_ROOT / ".env")),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Provider
    llm_provider: Literal["openai", "bedrock"] = "openai"
    openai_api_key: str = ""

    # Model routing
    model_plan: str = "gpt-4o-mini"
    model_draft: str = "gpt-4o"
    model_reviewer: str = "gpt-4o-mini"
    model_rewrite: str = "gpt-4o"
    model_style: str = "gpt-4o-mini"
    model_final: str = "gpt-4o"
    model_quiz: str = "gpt-4o-mini"
    model_image: str = "gpt-image-1"

    # Reviewer diversity
    diversity_provider: bool = False
    model_reviewer_technical_alt: str = ""
    model_reviewer_style_alt: str = ""
    model_reviewer_structure_alt: str = ""
    model_reviewer_grounding_alt: str = ""
    model_reviewer_reader_alt: str = ""

    # Images
    image_count: int = Field(default=4, ge=0, le=8)
    image_count_max: int = Field(default=5, ge=1, le=8)
    image_aspect_ratio: str = "16:9"
    image_quality: str = "hd"

    # Pipeline limits
    max_review_iterations: int = Field(default=12, ge=1)
    max_style_pass: int = Field(default=2, ge=1)
    max_grounding_recheck: int = Field(default=2, ge=1)
    max_image_redraw: int = Field(default=2, ge=0, le=4)
    max_editor_retries: int = Field(default=2, ge=0, le=4)
    editor_score_threshold: float = Field(default=8.0, ge=1.0, le=10.0)

    # Style guide — path relative to BACKEND_ROOT
    medium_style_guide_path: str = "skills/medium.md"
    medium_style_guide_required: bool = True

    # Persistence
    database_url: str = "sqlite:///./data/medium_agent.db"
    checkpoint_db_path: str = "./data/checkpoints.db"

    # Observability
    tracing_enabled: bool = False
    langsmith_api_key: str = ""
    langsmith_project: str = "medium-article-agent"

    # AWS Bedrock
    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    bedrock_model_plan: str = ""
    bedrock_model_draft: str = ""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors(cls, v: str | list[str]) -> str:
        if isinstance(v, list):
            return ",".join(v)
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def style_guide_path(self) -> Path:
        return BACKEND_ROOT / self.medium_style_guide_path

    @property
    def data_dir(self) -> Path:
        d = BACKEND_ROOT / "data"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def prompts_dir(self) -> Path:
        return BACKEND_ROOT / "prompts"

    @property
    def checkpoint_path(self) -> Path:
        p = Path(self.checkpoint_db_path)
        if not p.is_absolute():
            p = BACKEND_ROOT / p
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def load_style_guide(self) -> str:
        path = self.style_guide_path
        if not path.exists() or path.stat().st_size == 0:
            if self.medium_style_guide_required:
                raise FileNotFoundError(
                    f"Medium style guide required but missing/empty: {path}"
                )
            return ""
        return path.read_text(encoding="utf-8")

    def style_guide_status(self) -> dict:
        path = self.style_guide_path
        if path.exists() and path.stat().st_size > 0:
            return {"loaded": True, "path": str(path), "chars": path.stat().st_size}
        return {"loaded": False, "path": str(path), "chars": 0}


@lru_cache
def get_settings() -> Settings:
    return Settings()
