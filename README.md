# Zelash AI Framework

🚀 **An autonomous LLM-governed project synthesis framework with hierarchical task decomposition and multi-agent collaboration.**

## 🌟 Overview

Zelash is a fully autonomous, LLM-governed project synthesis framework that performs stratified abstraction parsing and hierarchical task resolution across semantically decoupled execution domains—backend, middleware, design, and frontend. Each stratum is instantiated through domain-specialized generative agents with sandboxed execution boundaries, minimizing inter-layer entropy.

A meta-controller LLM persistently supervises stateful build progression, performing latent error diagnosis, rollback-aware dependency resolution, and regenerative code healing—culminating in a deterministic, repo-synced, production-grade codebase with minimal human dependency.

## ✨ Key Features

- **🧠 Hierarchical Task Decomposition**: Break down complex tasks into manageable subtasks
- **🤝 Multi-Agent Collaboration**: Specialized agents for research, analysis, and content generation
- **🛠️ Tool Augmentation**: Empower agents with web search, browser automation, and data visualization
- **🔌 Model Control Protocol (MCP)**: Sandboxed execution with remote tool execution capability
- **🌐 Browser Automation**: Integrated Playwright-based web automation
- **🎨 Multiple UI Options**: API server, CLI, and modern Gradio web interface
- **🔍 Advanced Research**: Google Custom Search integration for comprehensive data gathering
- **📊 Data Visualization**: Built-in chart generation and analysis capabilities

## 🏗️ Architecture

Zelash uses a sophisticated 3-layer architecture:

### 1. **Repository Layer** (`src/repository/`)
- **Agents**: Specialized domain agents (backend, frontend, middleware, design, research, analysis, writing)
- **LLM Integration**: Support for Gemini, OpenAI, Anthropic, and AWS Bedrock
- **Tools**: Web search, browser automation, data processing, and visualization tools
- **Execution**: Sandboxed code execution and task orchestration
- **MCP Server**: Model Control Protocol server for tool communication

### 2. **Service Layer** (`src/service/`)
- **Agent Service**: Orchestrates multi-agent workflows
- **LLM Factory**: Manages multiple LLM providers with failover
- **Tool Service**: Handles tool registration and execution

### 3. **API Layer** (`src/api/`)
- **Agent Controller**: RESTful API for agent interactions
- **Tool Controller**: API endpoints for tool management

## 🔧 Installation

### Prerequisites
- Python 3.8+ 
- Git

### Setup Steps

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/zelash.git
cd zelash
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables:**
```bash
cp .env.example .env
# Edit .env with your API keys
```

### Required API Keys
- **Gemini API**: Google AI Studio key for Gemini models
- **OpenAI API**: OpenAI API key for GPT models  
- **Anthropic API**: Anthropic key for Claude models
- **Google Search API**: For web search functionality
- **AWS Credentials**: For Bedrock models (optional)

## 🚀 Usage

### 🌐 Web UI Mode (Recommended)
Launch the modern Gradio-based web interface:

```bash
python -m src.main --mode web
# Access at http://localhost:7788
```

**Web UI Features:**
- Interactive chat interface with specialized agents
- Real-time browser automation visualization
- Task progress tracking and monitoring
- Theme customization (Ocean, Soft, Monochrome themes)
- File upload and download capabilities

### 🖥️ API Server Mode
Start the FastAPI server for programmatic access:

```bash
python -m src.main --mode api --port 8000
# API docs at http://localhost:8000/docs
```

**API Endpoints:**
- `POST /agents/run` - Execute agent tasks
- `GET /agents/status` - Check agent status
- `POST /tools/execute` - Run tools directly
- `GET /health` - Health check endpoint

### 💻 CLI Mode
Run tasks from the command line:

```bash
python -m src.main --mode cli
```

### 🐳 Docker Deployment
Run with Docker (includes all dependencies):

```bash
# Standard deployment
docker-compose up -d

# ARM64 support (Apple Silicon)
docker build -f Dockerfile.arm64 -t zelash-arm64 .
docker run -p 7788:7788 zelash-arm64
```

## 🤖 Specialized Agents

Zelash includes domain-specific agents optimized for different tasks:

### Core Agents
- **🔬 Research Agent**: Web research, data gathering, and information synthesis
- **📊 Analysis Agent**: Data analysis, pattern recognition, and insights generation  
- **✍️ Writing Agent**: Content creation, documentation, and technical writing
- **🎨 Design Agent**: UI/UX design, wireframing, and visual planning

### Development Agents  
- **⚙️ Backend Agent**: Server-side development, APIs, and database design
- **🎨 Frontend Agent**: User interface development and client-side logic
- **🔗 Middleware Agent**: Integration services and business logic
- **🛠️ Tool Call Agent**: Dynamic tool execution and automation

## 🛠️ Integrated Tools

### Browser Automation (`integrations/browser-use/`)
- **Playwright Integration**: Full browser automation capabilities
- **Dynamic Web Interaction**: Click, type, scroll, and navigate web pages
- **Screenshot Capture**: Visual verification and debugging
- **Data Extraction**: Scrape and parse web content intelligently

### Model Control Protocol (`integrations/mcp-browser-use/`)
- **Sandboxed Execution**: Secure tool execution environment
- **Remote Tool Access**: Execute tools across different environments
- **Protocol Compliance**: Full MCP specification support

### Web Research Tools
- **Google Custom Search**: Comprehensive web search capabilities
- **Content Extraction**: Intelligent parsing of web articles and documents
- **Real-time Data**: Access to current information and trends

### Data Processing
- **Pandas Integration**: Advanced data manipulation and analysis
- **Matplotlib Visualization**: Chart generation and data visualization
- **Export Capabilities**: Multiple output formats (CSV, JSON, images)

## 📁 Project Structure

```
zelash/
├── src/                          # Core application code
│   ├── main.py                   # Main entry point
│   ├── api/                      # REST API controllers
│   │   ├── agent_controller.py   # Agent management endpoints
│   │   └── tool_controller.py    # Tool execution endpoints
│   ├── repository/               # Core business logic
│   │   ├── agent/               # Specialized agent implementations
│   │   ├── llm/                 # LLM provider integrations
│   │   ├── tools/               # Tool implementations
│   │   ├── execution/           # Task execution engine
│   │   ├── mcp/                 # Model Control Protocol
│   │   └── deployment/          # CLI and web UI components
│   ├── service/                 # Service layer
│   │   ├── agent_service.py     # Agent orchestration
│   │   ├── llm_factory.py       # Multi-provider LLM management
│   │   └── tool_service.py      # Tool management
│   └── schemas/                 # Data models and validation
├── integrations/                # External integrations
│   ├── browser-use/             # Browser automation framework
│   └── mcp-browser-use/         # MCP server implementation
├── web-ui/                      # Gradio web interface
├── browser-automation/          # Additional browser tools
└── requirements.txt             # Python dependencies
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root with the following configuration:

```bash
# LLM API Keys
GEMINI_API_KEY=your_google_ai_api_key_here
OPENAI_API_KEY=your_openai_api_key_here  
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Model Selection
GEMINI_MODEL=gemini-2.0-flash
OPENAI_MODEL=gpt-4o
ANTHROPIC_MODEL=claude-3-sonnet

# AWS Bedrock (Optional)
AWS_REGION=us-east-1
BEDROCK_MODEL=anthropic.claude-v2
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# Google Search API
GOOGLE_SEARCH_API_KEY=your_google_api_key
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id

# Server Configuration  
HOST=0.0.0.0
PORT=8000
DEBUG=True
LOG_LEVEL=INFO
```

### Model Providers

Zelash supports multiple LLM providers with automatic failover:

1. **Google Gemini**: Primary recommendation for balanced performance
2. **OpenAI GPT**: Excellent for complex reasoning tasks
3. **Anthropic Claude**: Strong safety and helpfulness focus
4. **AWS Bedrock**: Enterprise-grade deployment option

## 📚 API Documentation

### Agent Execution

```python
# Execute a research task
POST /agents/run
{
    "agent_type": "research",
    "query": "Latest developments in AI safety",
    "tools": ["web_search", "browser_automation"]
}
```

### Tool Management

```python
# List available tools
GET /tools/

# Execute a specific tool
POST /tools/execute
{
    "tool_name": "web_search",
    "parameters": {
        "query": "machine learning trends 2025",
        "num_results": 10
    }
}
```

## 🧪 Examples

### Research and Analysis Workflow

```python
# 1. Research phase
research_result = agent_service.run_agent(
    agent_type="research",
    query="Analyze current trends in sustainable energy",
    tools=["web_search", "data_visualization"]
)

# 2. Analysis phase  
analysis_result = agent_service.run_agent(
    agent_type="analysis", 
    query=f"Analyze this research data: {research_result}",
    tools=["data_processing", "chart_generation"]
)

# 3. Content creation
final_report = agent_service.run_agent(
    agent_type="writing",
    query=f"Create comprehensive report: {analysis_result}",
    tools=["document_generation"]
)
```

### Browser Automation Example

```python
# Automate web data collection
browser_result = agent_service.run_agent(
    agent_type="tool_call",
    query="Extract pricing data from competitors",
    tools=["browser_automation", "data_extraction"]
)
```

## 🔧 Development

### Setting Up Development Environment

```bash
# Clone and setup
git clone https://github.com/yourusername/zelash.git
cd zelash

# Create virtual environment
python -m venv test_venv
source test_venv/bin/activate  # macOS/Linux
# or test_venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install development dependencies  
pip install pytest pytest-asyncio

# Run tests
pytest tests/
```

### Adding Custom Agents

1. **Create Agent Class**: Inherit from `BaseAgent`
2. **Implement Methods**: Define `run()` method
3. **Register Agent**: Add to agent factory
4. **Test Integration**: Write unit tests

```python
from src.repository.agent.base_agent import BaseAgent

class CustomAgent(BaseAgent):
    def __init__(self, llm, verbose=False):
        super().__init__(
            llm=llm,
            system_prompt="Your custom system prompt",
            name="custom_agent",
            verbose=verbose
        )
    
    def run(self, user_query):
        # Implement your custom logic
        return self.llm.generate_response(
            system_prompt=self.system_prompt,
            user_prompt=user_query
        )
```

### Adding Custom Tools

```python
from src.repository.tools.base_tool import BaseTool

class CustomTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="custom_tool",
            description="Description of your tool"
        )
    
    def execute(self, **kwargs):
        # Implement tool logic
        return {"result": "Tool output"}
```

## 🐛 Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure all required API keys are set in `.env`
2. **Port Conflicts**: Change port in configuration if 8000/7788 are in use
3. **Browser Issues**: Install Playwright browsers: `playwright install`
4. **Memory Issues**: Reduce concurrent agent count for lower-spec machines

### Debug Mode

Enable detailed logging:

```bash
export DEBUG=True
export LOG_LEVEL=DEBUG
python -m src.main --mode web
```

### Performance Optimization

- **Concurrent Agents**: Limit to 2-3 for optimal performance
- **Tool Caching**: Enable result caching for repeated operations
- **Model Selection**: Use Gemini Flash for faster responses

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/test_agents.py          # Agent functionality
pytest tests/test_controller.py      # API endpoints  
pytest tests/test_helpers.py         # Utility functions
pytest tests/test_llm_api.py         # LLM integrations
pytest tests/test_playwright.py      # Browser automation

# Run with coverage
pytest --cov=src tests/
```

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**: 
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**: Follow the coding standards
4. **Add tests**: Ensure new features have proper test coverage
5. **Run tests**: 
   ```bash
   pytest tests/
   ```
6. **Commit changes**: 
   ```bash
   git commit -m 'Add amazing feature'
   ```
7. **Push to branch**: 
   ```bash
   git push origin feature/amazing-feature
   ```
8. **Open a Pull Request**: Describe your changes clearly

### Coding Standards

- **Python Style**: Follow PEP 8 guidelines
- **Documentation**: Add docstrings for all public methods
- **Type Hints**: Use type annotations where appropriate
- **Testing**: Maintain >80% test coverage
- **Commit Messages**: Use conventional commit format

### Areas for Contribution

- 🧠 **New Agent Types**: Domain-specific agents for specialized tasks
- 🛠️ **Additional Tools**: Integrations with external services
- 🎨 **UI Improvements**: Enhanced web interface features
- 📚 **Documentation**: Tutorials, examples, and guides
- 🧪 **Testing**: Improved test coverage and edge cases
- 🚀 **Performance**: Optimization and scalability improvements

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Browser-Use**: Playwright-based browser automation framework
- **Model Control Protocol**: Anthropic's MCP specification
- **Gradio**: Modern web UI framework
- **FastAPI**: High-performance API framework
- **All Contributors**: Thanks to everyone who has contributed to this project

## 📞 Support

- 📚 **Documentation**: Check this README and inline code comments
- 🐛 **Issues**: Report bugs via GitHub Issues
- 💬 **Discussions**: Join GitHub Discussions for questions
- 📧 **Contact**: Reach out for enterprise support

## 🚀 Roadmap

### Upcoming Features

- **🧠 Advanced Agent Orchestration**: Improved multi-agent workflows
- **🔌 Plugin System**: Extensible architecture for custom integrations
- **📊 Analytics Dashboard**: Real-time monitoring and metrics
- **🌍 Multi-language Support**: Internationalization capabilities
- **🔒 Enhanced Security**: Advanced authentication and authorization
- **☁️ Cloud Deployment**: One-click cloud deployment options

### Long-term Vision

Zelash aims to become the premier autonomous project synthesis framework, enabling users to transform ideas into fully-functional applications through intelligent agent collaboration and sophisticated tool integration.

---

**Built with ❤️ by the Zelash team**

*Empowering autonomous development through intelligent agent collaboration*
