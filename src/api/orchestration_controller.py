from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, Any
import asyncio
import json

from src.service.build_service import BuildManager, serialize_build
from src.service.llm_factory import LLMFactory
from src.service.tool_service import ToolService


class BuildRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Plain-language project goal")


class OrchestrationController:
    """REST API controller for the autonomous build pipeline."""

    def __init__(self, app: FastAPI, llm_factory: LLMFactory, tool_service: ToolService):
        self.app = app
        self.manager = BuildManager(llm_factory, tool_service)
        self._register_routes()

    def _register_routes(self) -> None:
        @self.app.get("/health")
        async def health() -> Dict[str, str]:
            return {"status": "ok"}

        @self.app.post("/api/build", response_model=Dict[str, Any])
        async def start_build(request: BuildRequest = Body(...)):
            try:
                state = self.manager.start_build(request.prompt)
                return {"build_id": state.build_id, "status": state.status}
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc))

        @self.app.post("/api/build/{build_id}/retry", response_model=Dict[str, Any])
        async def retry_build(build_id: str):
            try:
                state = self.manager.retry_build(build_id)
                return serialize_build(state)
            except KeyError:
                raise HTTPException(status_code=404, detail=f"Build not found: {build_id}")

        @self.app.get("/api/build/{build_id}/status", response_model=Dict[str, Any])
        async def build_status(build_id: str):
            state = self.manager.get_build(build_id)
            if not state:
                raise HTTPException(status_code=404, detail=f"Build not found: {build_id}")
            return serialize_build(state)

        @self.app.get("/api/build/{build_id}/logs")
        async def build_logs(build_id: str, stream: bool = False):
            state = self.manager.get_build(build_id)
            if not state:
                raise HTTPException(status_code=404, detail=f"Build not found: {build_id}")
            if not stream:
                return {"build_id": build_id, "logs": self.manager.get_logs(build_id)}

            async def event_stream():
                seen = 0
                while True:
                    current = self.manager.get_build(build_id)
                    if not current:
                        break
                    for line in current.logs[seen:]:
                        yield f"data: {json.dumps({'message': line})}\n\n"
                    seen = len(current.logs)
                    if current.status in {"completed", "failed"}:
                        yield f"event: done\ndata: {json.dumps({'status': current.status})}\n\n"
                        break
                    await asyncio.sleep(0.5)

            return StreamingResponse(event_stream(), media_type="text/event-stream")

        @self.app.get("/api/builds", response_model=Dict[str, Any])
        async def list_builds():
            return {"builds": [serialize_build(build) for build in self.manager.list_builds()]}

        @self.app.get("/api/build/{build_id}/result", response_model=Dict[str, Any])
        async def build_result(build_id: str):
            state = self.manager.get_build(build_id)
            if not state:
                raise HTTPException(status_code=404, detail=f"Build not found: {build_id}")
            if state.status != "completed" or not state.result:
                raise HTTPException(status_code=409, detail=f"Build is not complete. Current status: {state.status}")
            return state.result
