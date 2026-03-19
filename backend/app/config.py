"""Application configuration management.

Reads from .env file and environment variables.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
WORKSPACE_ROOT = BASE_DIR / "workspace"

# Load .env into OS environment BEFORE pydantic-settings reads env vars
load_dotenv(BASE_DIR / ".env", override=False)

from pydantic import Field
from pydantic_settings import BaseSettings


class LLMConfig(BaseSettings):
    """LLM API configuration."""

    provider: str = "openai"  # options: openai, deepseek, minimax, qwen, doubao
    model: str = "gpt-4o"
    base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    max_tokens: int = 4096
    temperature: float = 0.0

    class Config:
        env_prefix = "LLM_"



class LLMVisionConfig(BaseSettings):
    """Vision LLM configuration (for image-based problem parsing)."""

    model: str = "gpt-4o"
    base_url: str = "https://api.openai.com/v1"
    api_key: str = ""

    class Config:
        env_prefix = "LLM_VISION_"


class DatabaseConfig(BaseSettings):
    """Database configuration."""

    # url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/mathagent"
    url: str = "sqlite+aiosqlite:///./mathagent.db"
    echo: bool = False

    class Config:
        env_prefix = "DB_"


class RedisConfig(BaseSettings):
    """Redis configuration."""

    url: str = "redis://localhost:6379/0"

    class Config:
        env_prefix = "REDIS_"


class SandboxConfig(BaseSettings):
    """Code execution sandbox configuration."""

    provider: str = "opensandbox"  # "opensandbox", "e2b", or "local"
    # OpenSandbox self-hosted server connection
    opensandbox_domain: str = "localhost:8080"
    opensandbox_api_key: str = ""
    opensandbox_image: str = "opensandbox/code-interpreter:v1.0.1"
    # E2B cloud sandbox
    e2b_api_key: str = ""
    timeout_seconds: int = 30

    class Config:
        env_prefix = "SANDBOX_"


class AuthConfig(BaseSettings):
    """Authentication configuration."""

    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    class Config:
        env_prefix = "AUTH_"


class AppConfig(BaseSettings):
    """Root application configuration."""

    app_name: str = "MathModelingAgent"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    workspace_root: str = str(WORKSPACE_ROOT)

    # Sub-configs
    llm: LLMConfig = Field(default_factory=LLMConfig)
    llm_vision: LLMVisionConfig = Field(default_factory=LLMVisionConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    sandbox: SandboxConfig = Field(default_factory=SandboxConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)

    class Config:
        env_prefix = "APP_"


# Singleton config instance
config = AppConfig()
