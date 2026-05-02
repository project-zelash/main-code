import time

from fastapi.testclient import TestClient

from src.main import create_app
from src.service.build_service import BuildManager, BuildState, PIPELINE_STAGES, StageState


class DummyFactory:
    pass


class DummyTools:
    pass


def test_build_api_completes_and_returns_result():
    app, *_ = create_app()
    client = TestClient(app)

    response = client.post("/api/build", json={"prompt": "build a simple landing page"})
    assert response.status_code == 200
    build_id = response.json()["build_id"]

    final_status = None
    for _ in range(50):
        status_response = client.get(f"/api/build/{build_id}/status")
        assert status_response.status_code == 200
        final_status = status_response.json()
        if final_status["status"] in {"completed", "failed"}:
            break
        time.sleep(0.1)

    assert final_status is not None
    assert final_status["status"] == "completed"
    assert all(stage["status"] == "completed" for stage in final_status["stages"])

    result_response = client.get(f"/api/build/{build_id}/result")
    assert result_response.status_code == 200
    result = result_response.json()
    assert result["live_url"].startswith("file://")
    assert "index.html" in result["files_created"]


def test_build_api_rejects_empty_prompt():
    app, *_ = create_app()
    client = TestClient(app)

    response = client.post("/api/build", json={"prompt": ""})
    assert response.status_code == 422


def test_build_history_lists_previous_builds():
    app, *_ = create_app()
    client = TestClient(app)

    client.post("/api/build", json={"prompt": "build history test"})
    response = client.get("/api/builds")

    assert response.status_code == 200
    assert "builds" in response.json()


def test_build_manager_retry_resets_failed_checkpoint(tmp_path):
    manager = BuildManager(DummyFactory(), DummyTools())
    manager.base_dir = tmp_path
    manager.builds_dir = tmp_path / "builds"
    manager.generated_dir = tmp_path / "generated"
    manager.builds_dir.mkdir()
    manager.generated_dir.mkdir()
    state = BuildState(
        build_id="retry-case",
        prompt="retry me",
        status="failed",
        created_at=time.time(),
        updated_at=time.time(),
        stages=[StageState(name=name) for name in PIPELINE_STAGES],
        failed_stage="Testing",
    )
    state.stages[6].status = "failed"
    state.stages[6].error = "broken"
    manager._builds[state.build_id] = state
    manager._run_pipeline = lambda build_id: None

    retried = manager.retry_build("retry-case")

    assert retried.status == "queued"
    assert retried.stages[6].status == "waiting"
    assert retried.stages[6].error is None
    assert retried.recovery_attempts == 1


def test_build_manager_auto_recovery_continues_after_stage_failure(tmp_path):
    manager = BuildManager(DummyFactory(), DummyTools())
    manager.base_dir = tmp_path
    manager.builds_dir = tmp_path / "builds"
    manager.generated_dir = tmp_path / "generated"
    manager.builds_dir.mkdir()
    manager.generated_dir.mkdir()
    now = time.time()
    state = BuildState(
        build_id="recover-case",
        prompt="recover me",
        status="queued",
        created_at=now,
        updated_at=now,
        stages=[StageState(name=name) for name in PIPELINE_STAGES],
    )
    manager._builds[state.build_id] = state
    original_run_stage = manager._run_stage
    failures = {"count": 0}

    def flaky_run_stage(current_state, index):
        if current_state.stages[index].name == "Integration" and failures["count"] == 0:
            failures["count"] += 1
            current_state.stages[index].status = "failed"
            current_state.stages[index].error = "transient integration failure"
            raise RuntimeError("transient integration failure")
        return original_run_stage(current_state, index)

    manager._run_stage = flaky_run_stage
    manager._run_pipeline(state.build_id)

    assert failures["count"] == 1
    assert state.status == "completed"
    assert state.recovery_attempts == 1
    assert state.result["live_url"].startswith("file://")


def test_build_manager_validation_failures_are_explicit(tmp_path):
    manager = BuildManager(DummyFactory(), DummyTools())
    manager.base_dir = tmp_path
    manager.builds_dir = tmp_path / "builds"
    manager.generated_dir = tmp_path / "generated"
    manager.builds_dir.mkdir()
    manager.generated_dir.mkdir()
    state = BuildState(
        build_id="validation-case",
        prompt="validate",
        status="queued",
        created_at=time.time(),
        updated_at=time.time(),
        stages=[StageState(name=name) for name in PIPELINE_STAGES],
    )
    manager._builds[state.build_id] = state

    try:
        manager._integration(state)
    except RuntimeError as exc:
        assert "Frontend artifact missing" in str(exc)
    else:
        raise AssertionError("Expected missing frontend artifact to fail")
