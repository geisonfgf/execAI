# execAI

**CLI AI Agent to run and schedule commands with natural language using AI**

execAI is a powerful command-line tool that lets you execute system commands and schedule tasks using natural language descriptions. Powered by AI and LangGraph, it provides a secure, intuitive interface for system administration and task automation.

## 🚀 Features

- **Natural Language Processing**: Describe what you want to do in plain English
- **AI-Powered Command Interpretation**: Uses GPT-4 to understand and convert requests to system commands
- **Secure Execution**: Safe mode with command validation and user confirmation
- **Task Scheduling**: Support for one-time and recurring tasks with cron expressions
- **Rich CLI Interface**: Beautiful terminal output with tables, panels, and progress indicators
- **Comprehensive Logging**: Detailed logging and error recovery mechanisms
- **Environment Configuration**: Secure configuration management with `.env` support

## 🛠️ Installation

### Requirements

- Python 3.8+
- OpenAI API key
- Unix-like system (Linux, macOS)

### Install from Source

```bash
# Clone the repository
git clone https://github.com/yourusername/execai.git
cd execai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Install development dependencies (optional)
pip install -e .[dev]
```

### Configuration

1. Copy the environment template:
```bash
cp env.example .env
```

2. Edit `.env` with your configuration:
```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-turbo-preview
SAFE_MODE=true
CONFIRMATION_REQUIRED=true
```

## 🎯 Usage

### Basic Commands

#### Execute a command
```bash
# Simple command execution
execai run "list all files in the current directory"

# Skip confirmation (use with caution)
execai run "show system information" --force

# Dry run (preview without execution)
execai run "create a backup of my documents" --dry-run
```

#### Schedule tasks
```bash
# Schedule a one-time task
execai run "backup my home directory tomorrow at 2 AM" --schedule

# Schedule recurring tasks
execai run "clean temporary files every day at midnight" --schedule

# Using cron expressions
execai run "update system packages every Sunday at 3 AM" --schedule
```

### Schedule Management

#### View scheduled tasks
```bash
execai schedules
```

#### Control schedules
```bash
# Pause a schedule
execai pause <schedule-id>

# Resume a schedule
execai resume <schedule-id>

# Cancel a schedule
execai cancel <schedule-id>
```

### System Information

#### Check status
```bash
execai status
```

#### View configuration
```bash
execai config
```

#### Show version
```bash
execai version
```

### CLI Options

- `--verbose, -v`: Enable verbose output
- `--debug`: Enable debug mode
- `--force, -f`: Skip confirmation prompts
- `--dry-run, -d`: Show what would be executed without running
- `--schedule, -s`: Schedule command instead of running immediately

## 🔒 Security Features

### Safe Mode

By default, execAI runs in safe mode, which:
- Restricts execution to a whitelist of safe commands
- Requires confirmation for potentially dangerous operations
- Validates all commands before execution
- Logs all activities for audit purposes

### Command Validation

The system validates commands through multiple layers:
1. **AI Safety Assessment**: GPT-4 evaluates command safety
2. **Whitelist Checking**: Commands are checked against safe command lists
3. **User Confirmation**: Dangerous commands require explicit confirmation
4. **Execution Monitoring**: Real-time monitoring of command execution

### Environment Security

- Secure storage of API keys and secrets
- Environment variable encryption
- Configurable execution timeouts
- Process isolation and cleanup

## 📋 Examples

### Common Use Cases

#### System Administration
```bash
# Check system resources
execai run "show me CPU and memory usage"

# Find large files
execai run "find files larger than 100MB in my home directory"

# Check disk space
execai run "show disk space usage for all mounted filesystems"
```

#### File Operations
```bash
# Organize files
execai run "organize my Downloads folder by file type"

# Create backups
execai run "create a compressed backup of my Documents folder"

# Find and clean temporary files
execai run "find and remove temporary files older than 7 days"
```

#### Scheduled Tasks
```bash
# Daily backups
execai run "backup my important files to external drive every day at 11 PM" --schedule

# Weekly cleanup
execai run "clean up temporary files and logs every Sunday at 2 AM" --schedule

# Monthly reports
execai run "generate system usage report on the first day of each month" --schedule
```

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/execai

# Run specific test category
pytest tests/unit/
pytest tests/integration/
```

### Test Structure

```
tests/
├── unit/                 # Unit tests
│   ├── domain/          # Domain entity tests
│   ├── application/     # Application layer tests
│   └── infrastructure/  # Infrastructure tests
├── integration/         # Integration tests
└── fixtures/           # Test fixtures
```

## 🏗️ Architecture

execAI follows Domain-Driven Design (DDD) principles:

```
src/execai/
├── domain/              # Core business logic
│   ├── entities/       # Domain entities
│   ├── services/       # Domain services
│   └── repositories/   # Repository interfaces
├── application/        # Application layer
│   ├── agents/         # LangGraph agents
│   ├── usecases/       # Use cases
│   └── config/         # Configuration
├── infrastructure/     # External concerns
│   ├── ai/            # AI service integration
│   ├── scheduler/     # Task scheduling
│   ├── executor/      # Command execution
│   └── storage/       # Data persistence
└── interfaces/        # User interfaces
    ├── cli/           # Command-line interface
    └── api/           # HTTP API (future)
```

### Key Components

- **Command Agent**: LangGraph-based AI agent for natural language processing
- **Command Executor**: Secure command execution with monitoring
- **Cron Scheduler**: Task scheduling and cron job management
- **Rich CLI**: Beautiful terminal interface with Typer and Rich

## 🔧 Development

### Setup Development Environment

```bash
# Install pre-commit hooks
pre-commit install

# Run linting
black src/ tests/
flake8 src/ tests/
mypy src/

# Run tests in watch mode
pytest-watch
```

### Code Quality

The project uses:
- **Black**: Code formatting
- **Flake8**: Linting
- **MyPy**: Static type checking
- **pytest**: Testing framework
- **pre-commit**: Git hooks

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Ensure all tests pass: `pytest`
5. Run linting: `black . && flake8 . && mypy .`
6. Commit your changes: `git commit -m 'Add amazing feature'`
7. Push to the branch: `git push origin feature/amazing-feature`
8. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** for providing the GPT-4 API
- **LangChain** and **LangGraph** for the AI agent framework
- **Typer** and **Rich** for the beautiful CLI interface
- **Pydantic** for data validation and settings management

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/execai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/execai/discussions)
- **Email**: your.email@example.com

---

⚠️ **Important**: Always review commands before execution, especially when disabling safe mode. execAI is a powerful tool that can modify your system.

🔐 **Security**: Never share your OpenAI API key or commit it to version control. Use environment variables and secure storage. 