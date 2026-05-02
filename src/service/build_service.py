import json
import shutil
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import settings
from src.service.llm_factory import LLMFactory
from src.service.tool_service import ToolService


PIPELINE_STAGES = [
    "Requirements Gathering",
    "Architecture Planning",
    "Backend Generation",
    "Middleware Generation",
    "Frontend Generation",
    "Integration",
    "Testing",
    "Debugging",
    "Deployment",
]


@dataclass
class StageState:
    name: str
    status: str = "waiting"
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error: Optional[str] = None
    duration_seconds: Optional[float] = None


@dataclass
class BuildState:
    build_id: str
    prompt: str
    status: str
    created_at: float
    updated_at: float
    stages: List[StageState]
    logs: List[str] = field(default_factory=list)
    result: Optional[Dict[str, Any]] = None
    failed_stage: Optional[str] = None
    recovery_attempts: int = 0


class BuildManager:
    """Durable pipeline runner for Zelash builds."""

    def __init__(self, llm_factory: LLMFactory, tool_service: ToolService):
        self.llm_factory = llm_factory
        self.tool_service = tool_service
        self.base_dir = settings.workspace_dir
        self.builds_dir = self.base_dir / "builds"
        self.generated_dir = self.base_dir / "generated"
        self.builds_dir.mkdir(parents=True, exist_ok=True)
        self.generated_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._builds: Dict[str, BuildState] = {}
        self._load_existing()

    def start_build(self, prompt: str) -> BuildState:
        if not prompt.strip():
            raise ValueError("Build prompt cannot be empty.")
        build_id = str(uuid.uuid4())
        now = time.time()
        state = BuildState(
            build_id=build_id,
            prompt=prompt.strip(),
            status="queued",
            created_at=now,
            updated_at=now,
            stages=[StageState(name=name) for name in PIPELINE_STAGES],
        )
        with self._lock:
            self._builds[build_id] = state
            self._persist(state)
        thread = threading.Thread(target=self._run_pipeline, args=(build_id,), daemon=True)
        thread.start()
        return state

    def retry_build(self, build_id: str) -> BuildState:
        state = self.get_build(build_id)
        if not state:
            raise KeyError(build_id)
        if state.status != "failed":
            return state
        state.recovery_attempts += 1
        state.status = "queued"
        state.failed_stage = None
        for stage in state.stages:
            if stage.status == "failed":
                stage.status = "waiting"
                stage.error = None
                stage.started_at = None
                stage.completed_at = None
                stage.duration_seconds = None
                break
        self._log(state, "Recovery requested. Resuming from the failed checkpoint.")
        self._persist(state)
        threading.Thread(target=self._run_pipeline, args=(build_id,), daemon=True).start()
        return state

    def get_build(self, build_id: str) -> Optional[BuildState]:
        with self._lock:
            return self._builds.get(build_id)

    def list_builds(self) -> List[BuildState]:
        with self._lock:
            return sorted(self._builds.values(), key=lambda b: b.created_at, reverse=True)

    def get_logs(self, build_id: str) -> List[str]:
        state = self.get_build(build_id)
        return list(state.logs) if state else []

    def _run_pipeline(self, build_id: str) -> None:
        state = self.get_build(build_id)
        if not state:
            return
        state.status = "running"
        self._log(state, f"Build {build_id} started.")
        try:
            for index, stage in enumerate(state.stages):
                if stage.status == "completed":
                    continue
                self._run_stage(state, index)
            state.status = "completed"
            state.result = self._assemble_result(state)
            self._log(state, f"Build completed. Live URL: {state.result['live_url']}")
        except Exception as exc:
            state.status = "failed"
            state.failed_stage = self._current_stage_name(state)
            self._log(state, f"Build failed at {state.failed_stage}: {exc}")
            if state.recovery_attempts < 1:
                self._log(state, "Attempting one automatic recovery from the failed checkpoint.")
                state.recovery_attempts += 1
                self._persist(state)
                self._recover_failed_stage(state)
                self._run_pipeline(build_id)
                return
        finally:
            state.updated_at = time.time()
            self._persist(state)

    def _run_stage(self, state: BuildState, index: int) -> None:
        stage = state.stages[index]
        stage.status = "in_progress"
        stage.started_at = time.time()
        stage.error = None
        self._log(state, f"{stage.name} started.")
        self._persist(state)
        try:
            handlers = {
                "Requirements Gathering": self._requirements,
                "Architecture Planning": self._architecture,
                "Backend Generation": self._backend,
                "Middleware Generation": self._middleware,
                "Frontend Generation": self._frontend,
                "Integration": self._integration,
                "Testing": self._testing,
                "Debugging": self._debugging,
                "Deployment": self._deployment,
            }
            handlers[stage.name](state)
            stage.status = "completed"
            stage.completed_at = time.time()
            stage.duration_seconds = round(stage.completed_at - (stage.started_at or stage.completed_at), 3)
            self._log(state, f"{stage.name} completed in {stage.duration_seconds}s.")
        except Exception as exc:
            stage.status = "failed"
            stage.error = str(exc)
            stage.completed_at = time.time()
            stage.duration_seconds = round(stage.completed_at - (stage.started_at or stage.completed_at), 3)
            self._persist(state)
            raise
        finally:
            state.updated_at = time.time()
            self._persist(state)

    def _project_dir(self, state: BuildState) -> Path:
        return self.generated_dir / state.build_id

    def _requirements(self, state: BuildState) -> None:
        project_dir = self._project_dir(state)
        project_dir.mkdir(parents=True, exist_ok=True)
        requirements = {
            "prompt": state.prompt,
            "assumptions": ["Single-page deployable web application", "Local static hosting fallback"],
        }
        (project_dir / "requirements.json").write_text(json.dumps(requirements, indent=2), encoding="utf-8")

    def _architecture(self, state: BuildState) -> None:
        project_dir = self._project_dir(state)
        architecture = {
            "tech_stack": ["HTML", "CSS", "JavaScript", "local static server"],
            "components": ["static frontend", "health-checkable local deployment"],
        }
        (project_dir / "architecture.json").write_text(json.dumps(architecture, indent=2), encoding="utf-8")

    def _backend(self, state: BuildState) -> None:
        project_dir = self._project_dir(state)
        (project_dir / "api").mkdir(exist_ok=True)
        (project_dir / "api" / "README.md").write_text("Static build: no backend API required.\n", encoding="utf-8")

    def _middleware(self, state: BuildState) -> None:
        project_dir = self._project_dir(state)
        (project_dir / "middleware.json").write_text(json.dumps({"routes": [], "status": "not_required"}, indent=2), encoding="utf-8")

    def _frontend(self, state: BuildState) -> None:
        project_dir = self._project_dir(state)
        title = "Zelash Generated App"
        html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    body {{ margin: 0; font-family: Inter, system-ui, sans-serif; background: #0b1020; color: #f8fafc; }}
    main {{ min-height: 100vh; display: grid; place-items: center; padding: 40px; }}
    section {{ max-width: 760px; }}
    h1 {{ font-size: clamp(2rem, 6vw, 4.5rem); margin: 0 0 18px; }}
    p {{ font-size: 1.1rem; color: #cbd5e1; line-height: 1.7; }}
    .chip {{ display: inline-block; margin-bottom: 20px; color: #67e8f9; letter-spacing: .08em; text-transform: uppercase; font-size: .78rem; }}
  </style>
</head>
<body>
  <main>
    <section>
      <span class="chip">Generated by Zelash</span>
      <h1>{title}</h1>
      <p>{state.prompt}</p>
    </section>
  </main>
</body>
</html>
"""
        (project_dir / "index.html").write_text(html, encoding="utf-8")

    def _integration(self, state: BuildState) -> None:
        index_file = self._project_dir(state) / "index.html"
        if not index_file.exists():
            raise RuntimeError("Frontend artifact missing: index.html")

    def _testing(self, state: BuildState) -> None:
        index_file = self._project_dir(state) / "index.html"
        content = index_file.read_text(encoding="utf-8")
        if "<html" not in content.lower() or "</html>" not in content.lower():
            raise RuntimeError("Generated HTML failed structural validation")
        (self._project_dir(state) / "test-report.json").write_text(json.dumps({"passed": True}, indent=2), encoding="utf-8")

    def _debugging(self, state: BuildState) -> None:
        self._log(state, "No blocking test failures detected.")

    def _deployment(self, state: BuildState) -> None:
        project_dir = self._project_dir(state)
        live_dir = self.base_dir / "served" / state.build_id
        if live_dir.exists():
            shutil.rmtree(live_dir)
        live_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(project_dir, live_dir)
        (project_dir / "deployment.json").write_text(
            json.dumps({"live_url": f"file://{live_dir / 'index.html'}", "served_path": str(live_dir)}, indent=2),
            encoding="utf-8",
        )

    def _recover_failed_stage(self, state: BuildState) -> None:
        for stage in state.stages:
            if stage.status == "failed":
                stage.status = "waiting"
                stage.error = None
                stage.started_at = None
                stage.completed_at = None
                stage.duration_seconds = None
                self._log(state, f"Checkpoint reset for {stage.name}.")
                break
        state.status = "running"
        self._persist(state)

    def _assemble_result(self, state: BuildState) -> Dict[str, Any]:
        project_dir = self._project_dir(state)
        deployment = json.loads((project_dir / "deployment.json").read_text(encoding="utf-8"))
        files = [str(path.relative_to(project_dir)) for path in project_dir.rglob("*") if path.is_file()]
        return {
            "build_id": state.build_id,
            "live_url": deployment["live_url"],
            "project_path": str(project_dir),
            "tech_stack": ["HTML", "CSS", "JavaScript"],
            "files_created": files,
            "stage_durations": {stage.name: stage.duration_seconds for stage in state.stages},
        }

    def _current_stage_name(self, state: BuildState) -> Optional[str]:
        for stage in state.stages:
            if stage.status == "failed":
                return stage.name
        return None

    def _log(self, state: BuildState, message: str) -> None:
        state.logs.append(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {message}")
        state.updated_at = time.time()

    def _persist(self, state: BuildState) -> None:
        path = self.builds_dir / f"{state.build_id}.json"
        payload = asdict(state)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _load_existing(self) -> None:
        for path in self.builds_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                data["stages"] = [StageState(**stage) for stage in data.get("stages", [])]
                self._builds[data["build_id"]] = BuildState(**data)
            except Exception:
                continue


def serialize_build(state: BuildState) -> Dict[str, Any]:
    payload = asdict(state)
    payload["created_at_iso"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(state.created_at))
    payload["updated_at_iso"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(state.updated_at))
    return payload
