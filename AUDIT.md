# Zelash Audit

Date: 2026-05-02

Scope reviewed: top-level documentation (`README.md`, `README_AUTOMATION.md`, `Progress.md`, `PROMPT_MANAGER_GUIDE.md`, `.env.example`), active Python sources under `src`, `config`, `tests`, root automation/browser scripts, and the vendored integration trees under `integrations`. The `integrations/browser-use` and `integrations/mcp-browser-use` directories are large upstream/vendor trees; issues below distinguish active Zelash failures from vendored example/test requirements.

## Critical Runtime Breakages

- `src/main.py` cannot import because `src/api/tool_controller.py` imports `ToolConfigUpdate`, `ToolRegistration`, and `MCPConnection` from `src.schemas.tool`, but those classes do not exist.
- `src/main.py` calls `ToolService(config=tool_config, llm_factory=llm_factory)`, but `ToolService.__init__` only accepts `config`; the same incompatible call exists in `src/api/orchestration_controller.py`.
- `src/api/orchestration_controller.py` creates a global engine with a hardcoded Windows path: `d:\Asmit\main-code-zelash\workspace`.
- `src/api/orchestration_controller.py` expects `OrchestrationEngine` to expose `project_id`, `current_status`, `project_name`, `initialize_project`, `plan_project`, `stop_execution`, `get_status`, and other state fields that do not exist on the current engine.
- `src/utils/automation_workflow.py` and `src/utils/project_generator.py` use absolute-style imports such as `from utils...`, `from service...`, and `from repository...`; these fail when imported as `src.utils.*`.
- `src/utils/automation_workflow.py` imports `DeploymentManager` from `utils.deployment_manager`, but the active class is `SmartDeploymentManager`; `DeploymentManager` is not defined.
- `automation_main.py` relies on path mutation to import `utils.*`; this works only for direct script execution and not package usage.
- `AgentController.create_agent` treats `CreateAgentRequest.config` as if it were an `AgentConfig`, but the schema defines it as `Optional[Dict[str, Any]]`; `request.config.id`, `.dict()`, and `.tools` will fail for normal requests.
- `AgentResponse` requires `description` and `status`, but controllers return different fields such as `tools` and omit required fields.
- `ToolResponse` requires `id` and `type`, but `ToolController` returns `name`, `description`, and `schema`.

## Missing / Incomplete LLM Integration

- `src/repository/llm/openai_llm.py` has an unimplemented `chat()` method (`pass`).
- `src/repository/llm/anthropic_llm.py` has an unimplemented `chat()` method (`pass`).
- `src/repository/llm/bedrock_llm.py` has unimplemented `chat()` and `_convert_messages()` methods (`pass`).
- `src/service/llm_factory.py` does not validate configured provider names or missing API keys before instantiating providers.
- The LLM layer has no shared retry policy for transient errors or rate limits.
- Gemini uses the deprecated `google.generativeai` package as a fallback and emits a deprecation warning; the dependency list includes both old and new Gemini SDKs.
- `AgentManager` hardcodes Gemini as the only provider and model, ignoring configured `LLM_PROVIDER`.
- `MetaPlanner` hardcodes Gemini and fails during construction if no Gemini key is present, even when OpenAI, Anthropic, or Bedrock is configured.

## Missing / Incomplete Agent Orchestration

- `GeneralAgent._get_default_system_prompt()` is unimplemented and returns `None`.
- `AgentService` only imports/registers general, research, analysis, writing, and tool-call agents; it does not expose backend, frontend, middleware, or design through the API layer.
- There is no design agent implementation even though documentation and requirements list one.
- `AgentManager` only registers backend, middleware, and frontend; it explicitly omits design and does not register research, analysis, or writing.
- `AgentManager.submit_task()` returns raw agent output and does not guarantee structured output with status, agent name, task ID, logs, files, or errors.
- `OrchestrationEngine.process_user_request()` is a stub that returns `"Workflow completed (stub)"` without planning, agent execution, testing, deployment, or recovery.
- `OrchestrationEngine.run_full_workflow()` plans and calls code generation, but does not deploy, test, debug, or return a live URL.
- `CodeGenerationCoordinator` contains duplicate methods (`build_task_context`, `get_agent_flow_status`) and has fallback parsing that can write arbitrary LLM prose into generated files.
- `CodeGenerationCoordinator.set_project_output_directory()` nests generated projects as `automation_workspace/projects/{project}/{project}`, which is surprising and inconsistent with deployment assumptions.
- `MetaPlanner.identify_layers()` maps design to frontend, masking the missing design agent instead of handling design explicitly.

## Pipeline Recovery Gaps

- There is no persistent checkpoint model for the complete pipeline stages.
- There is no resume-from-last-successful-stage flow.
- Failures are recorded in scattered dictionaries/logs, but no central recovery state is persisted.
- The pipeline does not diagnose failures into repair actions and then continue from the failed stage.
- `ProgressIssueTracker` exists but is not wired into a durable end-to-end recovery controller.
- `BuildTestManager` is only partially connected from `OrchestrationEngine` and receives `None` for testing framework and feedback analyzer.

## Browser Automation Issues

- `direct_browser_automation.py` and `browser_automation_with_status.py` are hardcoded Google search demos, not reusable generated-application testers.
- Browser scripts write screenshots (`search_results.png`, `target_page.png`, `google_homepage.png`, etc.) into the repository root.
- `browser_automation_with_status.py` uses `signal.SIGALRM`, which is not portable to Windows.
- The automation path installs Playwright Chromium at runtime from `DirectPlaywrightTester.__init__`, which can add long network side effects to normal construction.
- Browser testing defaults to visible browser windows in some places, which is unsuitable for CI/server operation.
- Browser testing has MCP fallback, but MCP import paths depend on the legacy Gradio `web_ui/src` layout.

## Deployment Issues

- `README.md` references Docker files and docker-compose usage that are not present at the repository root.
- `src/utils/deployment_manager.py` has extensive deployment logic, but the primary orchestration engine does not call it.
- The minimum deployment guarantee, returning a local live URL, is not provided by `OrchestrationEngine.run_full_workflow()`.
- Generated project path conventions between `ProjectGenerator`, `CodeGenerationCoordinator`, and deployment detection are inconsistent.

## Environment / Configuration Issues

- `.env.example` is missing variables referenced by code: `LLM_PROVIDER`, `GEMINI_ANALYSIS_MODEL`, `ORCHESTRATION_PROMPT`, `AUTOMATION_WORKSPACE`, `AUTOMATION_REPORTS`, `BROWSER_HEADLESS`, `BROWSER_TIMEOUT`, `DEPLOYMENT_TIMEOUT`, `DEFAULT_PORT_RANGE`, MCP URL/settings, and frontend API URL settings.
- `.env.example` has no comments/descriptions for most operational variables.
- `VITE_GEMINI_API_KEY` is present but belongs to the old Vite demo frontend and is not appropriate for API-key handling in a backend-governed system.
- There is no central config loader. Environment reads are scattered across `src/main.py`, LLM classes, prompt manager, feedback analyzer, automation, deployment, and integrations.
- `PROMPT_MANAGER_GUIDE.md` contains hardcoded local paths under `/Users/saivishwasgooty/Documents/Projects/Hackathon/main-code`.
- `README.md` contains outdated install/run commands and references `web-ui` while the folder is `web_ui`.

## Dependency Issues

- `requirements.txt` pins `playwright==1.35.0`, which is old relative to modern browser automation and likely to download older browser binaries.
- `requirements.txt` does not include packages used by imported code/tests such as `httpx` for FastAPI tests and likely `pytest-cov` for coverage.
- `requirements.txt` includes both `google-generativeai` and `google-genai`; the old SDK should not be the primary path.
- Vendored browser-use and MCP integration have their own dependency metadata (`pyproject.toml`, `uv.lock`) that is not reconciled with the root `requirements.txt`.

## Test Suite Issues

- `tests/conftest.py` is empty.
- `tests/repository/execution/test_orchestration_engine.py` is empty.
- Root-level test scripts are mixed into the repository root instead of living under `tests`.
- Several tests skip broad failures instead of asserting behavior, so a broken system can appear acceptable.
- There are no focused tests for LLM factory provider selection and missing-key errors.
- There are no focused tests for checkpoint persistence/resume recovery.
- There are no API tests for the required build endpoints: `POST /api/build`, `GET /api/build/{id}/status`, `GET /api/build/{id}/logs`, `GET /api/builds`, `GET /api/build/{id}/result`.
- Coverage for core pipeline logic is below the requested 80% threshold because the key tests are empty or skip on dependency problems.

## Frontend Issues

- The root frontend is a Vite React chat UI, not the requested Next.js mission-control dashboard.
- The existing `web_ui` folder is a legacy Python/Gradio browser-use UI, not a Next.js TypeScript/Tailwind app.
- There are no pages for Home, Live Build, Results, History, or Settings in the requested Next.js structure.
- There is no REST/SSE contract between a frontend and backend for live build status/log streaming.

## Repository Hygiene Issues

- Root contains ad hoc scripts and outputs: `simple_browser_test.py`, `test_end_to_end.py`, `system_status.py`, `test_direct_playwright.py`, `manual_*`, `example_prompt_usage.py`, `external_repo_integration_example.py`, multiple `test_report_e2e_*.json`, `system_status_report.json`, and `test_batch.json`.
- `.gitignore` needs confirmation/update for `venv_312`, `.env`, `node_modules`, Playwright outputs, generated automation workspace, Python caches, and frontend build artifacts.
- `src/utils/build_test_manager.py` is empty while another `BuildTestManager` exists under `src/repository/execution`.

## Vendored Integration Notes

- `integrations/browser-use` includes many examples and tests that require external API keys (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `DEEPSEEK_API_KEY`, etc.). These should not be run as part of the Zelash core test suite unless explicitly enabled.
- `integrations/mcp-browser-use` has its own settings model and `.env.example` using `MCP_*` variables; root configuration does not currently document how Zelash maps or invokes those.
- Vendored integration tests include live browser/LLM/network tests and should be isolated from default CI.

