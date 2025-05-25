# Complete Automation Workflow System

A comprehensive system that automates the entire development lifecycle: **Generate → Deploy → Test → Report**.

## 🚀 Features

- **Project Generation**: AI-powered project creation using existing orchestration engine
- **Smart Deployment**: Auto-detects project types and handles deployment (15+ frameworks supported)
- **Browser Testing**: AI-driven testing using MCP browser automation with Playwright fallback
- **Comprehensive Reporting**: Detailed test results and workflow analytics
- **Batch Processing**: Run multiple workflows simultaneously
- **History Tracking**: Track and manage all workflow executions

## 📋 Quick Start

### Basic Usage

```bash
# Generate, deploy, and test a single project
python automation_main.py generate-deploy-test --prompt "Create a React todo app with TypeScript"

# Run with specific project type and custom tests
python automation_main.py generate-deploy-test \
  --prompt "Create a Flask API for user management" \
  --project-type flask \
  --test-scenarios "Test user creation" "Test user authentication"
```

### Batch Processing

```bash
# Create example configuration
python automation_main.py create-example-config --output my_batch.json

# Run batch workflows
python automation_main.py batch-workflow --config my_batch.json
```

### Workflow Management

```bash
# List all workflow history
python automation_main.py list-workflows

# Clean up specific workflow
python automation_main.py cleanup --workflow-id abc123

# Clean up all workflows
python automation_main.py cleanup --all
```

## 🏗️ Architecture

### Core Components

1. **ProjectGenerator** (`src/utils/project_generator.py`)
   - Integrates with existing OrchestrationEngine
   - Supports 4 prompt input methods (text, file, URL, interactive)
   - Project analysis and deployment readiness assessment

2. **SmartDeploymentManager** (`src/utils/deployment_manager.py`)
   - Auto-detects project types (NextJS, React, Vue, Django, Flask, Go, Java, etc.)
   - Handles installation, building, and service startup
   - Port detection and health checking

3. **BrowserTestingManager** (`src/utils/browser_testing_manager.py`)
   - MCP browser-use integration for AI-powered testing
   - Playwright fallback for direct browser automation
   - Comprehensive test suites (connectivity, UI, functionality, responsive design)

4. **AutomationWorkflow** (`src/utils/automation_workflow.py`)
   - Orchestrates the complete pipeline
   - Workflow history and reporting
   - Batch processing and cleanup operations

### Supported Project Types

- **Frontend**: React, Vue, Angular, NextJS, Svelte, Static HTML
- **Backend**: Django, Flask, FastAPI, Express, Go, Java Spring
- **Full-Stack**: NextJS, Nuxt, SvelteKit
- **Others**: Rust, Python scripts, Node.js applications

## 📊 Configuration

### Batch Configuration Format

```json
{
  "workflows": [
    {
      "prompt": "Create a React todo app with TypeScript",
      "project_type": "react",
      "test_scenarios": [
        "Test adding a new todo item",
        "Test marking todo as complete",
        "Test deleting a todo item"
      ]
    },
    {
      "prompt": "Create a Python Flask API for user management",
      "project_type": "flask",
      "test_scenarios": [
        "Test API endpoints are accessible",
        "Test user creation endpoint"
      ]
    }
  ]
}
```

### Environment Variables

```bash
# Optional: Custom paths
export AUTOMATION_WORKSPACE="/path/to/workspace"
export AUTOMATION_REPORTS="/path/to/reports"

# Optional: Browser testing configuration
export BROWSER_HEADLESS=true
export BROWSER_TIMEOUT=30000

# Optional: Deployment configuration
export DEPLOYMENT_TIMEOUT=300
export DEFAULT_PORT_RANGE="3000-8000"
```

## 🔧 Advanced Usage

### Programmatic API

```python
from src.utils.automation_workflow import AutomationWorkflow

# Initialize workflow
workflow = AutomationWorkflow()

# Run single workflow
result = await workflow.run_complete_workflow(
    prompt="Create a React app",
    project_type="react",
    test_scenarios=["Test homepage loads"]
)

# Run batch workflows
batch_config = [
    {"prompt": "Create app 1", "project_type": "react"},
    {"prompt": "Create app 2", "project_type": "flask"}
]
results = await workflow.run_batch_workflow(batch_config)

# Get workflow history
history = workflow.get_workflow_history()

# Cleanup
workflow.cleanup_workflow("workflow_id")
```

### Custom Test Scenarios

You can define custom test scenarios for more specific testing:

```python
test_scenarios = [
    "Navigate to homepage and verify title",
    "Test user registration form",
    "Test login functionality",
    "Test responsive design on mobile",
    "Test API endpoint /api/users returns JSON",
    "Test error handling for invalid inputs"
]
```

## 📈 Reporting

### Workflow Reports

Each workflow generates comprehensive reports including:

- **Generation Report**: File analysis, project structure, detected frameworks
- **Deployment Report**: Build logs, deployment status, service URLs
- **Test Report**: Test results, screenshots, performance metrics
- **Overall Summary**: Success/failure status, timing, recommendations

### Report Structure

```
reports/
├── workflow_abc123/
│   ├── workflow_summary.json
│   ├── generation_report.json
│   ├── deployment_report.json
│   ├── test_report.json
│   ├── screenshots/
│   └── logs/
```

## 🛠️ Integration

### Existing System Integration

This automation system integrates with existing components:

- **OrchestrationEngine**: For project generation
- **BashTool**: For secure command execution
- **PromptManager**: For dynamic prompt handling
- **BuildEnvironment**: For deployment detection
- **MCP Browser-Use**: For AI-powered browser testing

### MCP Server Integration

The system leverages the existing MCP server setup for browser automation:

```python
# Automatic integration with MCP browser-use
# No additional setup required - uses existing configuration
```

## 🚨 Error Handling

The system includes comprehensive error handling:

- **Generation Errors**: Retry with modified prompts, fallback strategies
- **Deployment Errors**: Auto-detection of missing dependencies, port conflicts
- **Testing Errors**: Fallback to Playwright, graceful test skipping
- **Cleanup Errors**: Safe resource cleanup, process termination

## 🔒 Security

- **Secure Command Execution**: Uses existing BashTool with security controls
- **Sandboxed Environments**: Each project runs in isolated environment
- **Port Management**: Automatic port allocation and conflict resolution
- **Process Management**: Proper cleanup of spawned processes

## 📝 Logging

Comprehensive logging is available at multiple levels:

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# View workflow logs
tail -f logs/automation_workflow.log

# View component-specific logs
tail -f logs/project_generator.log
tail -f logs/deployment_manager.log
tail -f logs/browser_testing.log
```

## 🤝 Contributing

This system is built on top of the existing codebase. When contributing:

1. Follow existing code patterns and structure
2. Ensure integration with existing components
3. Add comprehensive error handling
4. Include logging and reporting
5. Test with multiple project types

## 📄 License

Follows the same license as the main project.

## 🆘 Troubleshooting

### Common Issues

1. **Generation Fails**
   - Check OrchestrationEngine configuration
   - Verify LLM API keys and endpoints
   - Review prompt format and content

2. **Deployment Fails**
   - Check for missing dependencies (Node.js, Python, etc.)
   - Verify port availability
   - Review project structure and build files

3. **Testing Fails**
   - Ensure MCP browser-use server is running
   - Check browser installation (Playwright)
   - Verify deployment URL accessibility

4. **Performance Issues**
   - Reduce batch size for batch workflows
   - Increase timeout values
   - Check system resources (CPU, memory)

### Debug Mode

Enable verbose output for troubleshooting:

```bash
python automation_main.py generate-deploy-test \
  --prompt "Create a React app" \
  --verbose \
  --debug
```

## 📞 Support

For issues and questions:

1. Check the troubleshooting section above
2. Review logs in the `logs/` directory
3. Check existing GitHub issues
4. Create a new issue with detailed logs and configuration
