# Zelash AI Framework

An autonomous LLM-governed project synthesis framework with hierarchical task decomposition and multi-agent collaboration.

## Overview

Zelash is a fully autonomous, LLM-governed project synthesis framework that performs stratified abstraction parsing and hierarchical task resolution across semantically decoupled execution domains—backend, middleware, design, and frontend. Each stratum is instantiated through domain-specialized generative agents with sandboxed execution boundaries, minimizing inter-layer entropy.

A meta-controller LLM persistently supervises stateful build progression, performing latent error diagnosis, rollback-aware dependency resolution, and regenerative code healing—culminating in a deterministic, repo-synced, production-grade codebase with minimal human dependency.

## Key Features

- **Hierarchical Task Decomposition**: Break down complex tasks into manageable subtasks
- **Multi-Agent Collaboration**: Specialized agents for research, analysis, and content generation
- **Tool Augmentation**: Empower agents with web search, browser automation, and data visualization
- **Model Control Protocol**: Sandboxed execution with remote tool execution capability
- **Multiple Deployment Options**: API server, CLI, and web interface

## Architecture

Zelash uses a 3-layer architecture:

1. **Repository Layer**: Core components (agents, LLMs, tools, execution)
2. **Service Layer**: Integration and management services
3. **API Layer**: External interfaces and controllers

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/zelash.git
cd zelash
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your API keys (see `.env.example`).

## Usage

### API Server Mode

```bash
python -m src.main --mode api --port 8000
```

### CLI Mode

```bash
python -m src.main --mode cli
```

### Web UI Mode

```bash
python -m src.main --mode web
```

## Environment Variables

See `.env.example` for required API keys and configuration options.

## License

MIT

## Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request


