import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    llm_provider: str
    host: str
    port: int
    debug: bool
    log_level: str
    workspace_dir: Path
    reports_dir: Path
    browser_headless: bool
    browser_timeout: int
    deployment_timeout: int
    default_port_range: str
    mcp_server_url: str

    @classmethod
    def load(cls) -> "Settings":
        workspace = Path(os.getenv("AUTOMATION_WORKSPACE", ROOT_DIR / "automation_workspace"))
        reports = Path(os.getenv("AUTOMATION_REPORTS", workspace / "reports"))
        return cls(
            llm_provider=os.getenv("LLM_PROVIDER", "gemini").strip().lower(),
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8000")),
            debug=_bool_env("DEBUG", False),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            workspace_dir=workspace,
            reports_dir=reports,
            browser_headless=_bool_env("BROWSER_HEADLESS", True),
            browser_timeout=int(os.getenv("BROWSER_TIMEOUT", "30000")),
            deployment_timeout=int(os.getenv("DEPLOYMENT_TIMEOUT", "300")),
            default_port_range=os.getenv("DEFAULT_PORT_RANGE", "3000-8999"),
            mcp_server_url=os.getenv("MCP_SERVER_URL", "ws://localhost:8765"),
        )

    def llm_config(self) -> Dict[str, Dict[str, Optional[str]]]:
        return {
            "default_provider": self.llm_provider,
            "gemini": {
                "api_key": os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
                "model": os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
                "temperature": float(os.getenv("LLM_TEMPERATURE", "0.7")),
            },
            "openai": {
                "api_key": os.getenv("OPENAI_API_KEY"),
                "model": os.getenv("OPENAI_MODEL", "gpt-4o"),
                "temperature": float(os.getenv("LLM_TEMPERATURE", "0.7")),
            },
            "anthropic": {
                "api_key": os.getenv("ANTHROPIC_API_KEY"),
                "model": os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest"),
                "temperature": float(os.getenv("LLM_TEMPERATURE", "0.7")),
            },
            "bedrock": {
                "region_name": os.getenv("AWS_REGION", "us-east-1"),
                "model": os.getenv("BEDROCK_MODEL", "anthropic.claude-3-sonnet-20240229-v1:0"),
                "temperature": float(os.getenv("LLM_TEMPERATURE", "0.7")),
                "credentials": None,
            },
        }

    def tool_config(self) -> Dict[str, Dict[str, object]]:
        return {
            "web_search": {
                "api_key": os.getenv("GOOGLE_SEARCH_API_KEY"),
                "engine_id": os.getenv("GOOGLE_SEARCH_ENGINE_ID"),
            },
            "browser_use": {},
            "bash": {
                "allowed_commands": [],
                "disallowed_commands": ["rm -rf", "sudo", "shutdown", "reboot", "mkfs", "dd if="],
            },
            "planning": {},
            "chart": {
                "script_path": str(ROOT_DIR / "src" / "chart_generator.js"),
            },
        }


settings = Settings.load()
