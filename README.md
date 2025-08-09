# MindNext Hooks System - Three-Layer Architecture

**Version**: 3.0 Three-Layer Architecture  
**Framework**: Event → Rule → Action Flow  
**Created**: 2025-08-09  

## 🎯 System Overview

MindNext Hooks System is a comprehensive, modular, and extensible hooks system for Claude Code, featuring a sophisticated three-layer architecture designed for global use and easy GitHub distribution.

## 🏗️ Three-Layer Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Event Layer   │ ───► │   Rule Layer    │ ───► │ Action Flow     │
│                 │    │                 │    │ Layer           │
│ • Event capture │    │ • Rule matching │    │ • Action exec   │
│ • Standardize   │    │ • Condition eval│    │ • Pipelines     │
│ • Context build │    │ • Priority sort │    │ • Error handling│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📁 System Structure

```
hooks/
├── 🚀 mindnext_hooks.py             # Main entry point (Three-Layer)
├── 📄 claude_settings_example.json  # Claude Code settings template
├── 📋 config/                       # Configuration files
│   ├── rules_config.json            # Rule definitions  
│   ├── pipelines_config.json        # Action pipelines
│   └── quality_config.json          # Quality settings
├── 🔧 flow_engine/                  # Three-Layer Engine
│   ├── event_layer.py               # Event processing
│   ├── rule_layer.py                # Rule matching  
│   ├── action_layer.py              # Action execution
│   ├── flow_coordinator.py          # System coordinator
│   └── actions/                     # Modular actions
│       ├── action_prompt.py         # Prompt analysis
│       ├── action_ai.py             # AI integration
│       ├── action_quality.py        # Code quality
│       ├── action_memory.py         # Knowledge graph
│       ├── action_notification.py   # Multi-channel alerts
│       ├── action_analysis.py       # Performance metrics
│       ├── action_conditional.py    # Flow control
│       └── action_utility.py        # Core components
└── 🗂️ cleanup/                      # Legacy code archive
```

## ✨ Key Features

### 🎯 **20+ Modular Action Executors**
- **action.prompt** - Prompt analysis and enhancement
- **action.ai** - AI-powered code analysis and suggestions
- **action.quality** - Comprehensive code quality checks
- **action.memory** - Knowledge graph integration
- **action.notification** - Multi-channel notifications
- **action.analysis** - Performance and usage analytics
- **action.conditional** - Flow control and circuit breakers
- **action.utility** - Core components (Buffer/Cache/AI SDK)

### 🧠 **Intelligent Rule Engine**
- Complex condition matching with DSL support
- Priority-based rule execution
- Rate limiting and circuit breakers
- Event pattern detection
- File type and content filtering

### 🔄 **Pipeline-Based Action Flows**
- Sequential and parallel execution
- Error handling and recovery
- Data flow between actions
- Conditional execution
- Timeout and retry mechanisms

### 💾 **Core Components**
- **Buffer**: Event buffering and queuing system
- **Cache**: High-performance caching with TTL
- **AI SDK**: Integrated AI capabilities for analysis

## 🚀 Quick Start

### Setup and Installation

1. **Configure Claude Code hooks** - Copy settings from `claude_settings_example.json` to your `~/.claude/settings.json`
2. **Update paths** - Replace `/path/to/` with actual installation path
3. **Install dependencies** - `pip install -r requirements.txt`
4. **Test system** - `python mindnext_hooks.py --test`

### Basic Usage

```bash
# Test the system
python mindnext_hooks.py --test

# Get system status  
python mindnext_hooks.py --status

# Export execution report
python mindnext_hooks.py --export-report

# Process hook event
echo '{"hook_event_name": "PostToolUse", "tool_name": "Write"}' | python mindnext_hooks.py
```

### Claude Code Integration

Add to your `~/.claude/settings.json` (see `claude_settings_example.json` for complete configuration):

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/mindnext_hooks.py PostToolUse"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command", 
            "command": "/path/to/mindnext_hooks.py UserPromptSubmit"
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/mindnext_hooks.py SessionStart"
          }
        ]
      }
    ]
  }
}
```

**Note**: Replace `/path/to/` with the actual path to your MindNext Hooks installation.

## ⚙️ Configuration

### Rules Configuration (`config/rules_config.json`)

Define intelligent rules with complex conditions:

```json
{
  "rules": [
    {
      "id": "quality_check_on_code_edit",
      "name": "Auto quality check after code modification",
      "enabled": true,
      "priority": 100,
      "event_types": ["PostToolUse"],
      "file_patterns": ["*.py", "*.js", "*.ts"],
      "conditions": [
        {
          "expression": "tool_name in ['Edit', 'Write', 'MultiEdit']",
          "type": "simple"
        }
      ],
      "actions": [
        "action.quality/operation=check",
        "action.notification/type=console&severity=info&message=Quality check completed"
      ],
      "cooldown_seconds": 30
    }
  ]
}
```

### Pipeline Configuration (`config/pipelines_config.json`)

Create sophisticated action workflows:

```json
{
  "pipelines": [
    {
      "pipeline_id": "code_quality_full_check",
      "name": "Complete Code Quality Check Pipeline",
      "parallel_execution": false,
      "steps": [
        {
          "action_id": "quality_check",
          "action_type": "action.quality",
          "parameters": {"operation": "check"},
          "required": true,
          "output_to": "quality_results"
        },
        {
          "action_id": "security_scan",
          "action_type": "action.quality", 
          "parameters": {"operation": "security_scan"},
          "condition": "quality_results.get('summary', {}).get('total_errors', 0) == 0"
        }
      ]
    }
  ]
}
```

## 🎮 Available Actions

### Quality Assurance
- **Format code** - Auto-format with language-specific tools
- **Lint code** - Static analysis and style checking
- **Security scan** - Detect security vulnerabilities
- **Dependency check** - Package vulnerability scanning
- **Similarity check** - Duplicate code detection

### AI Enhancement
- **Code analysis** - AI-powered code review
- **Generate suggestions** - Improvement recommendations  
- **Detect patterns** - Architecture pattern detection
- **Estimate effort** - Development time estimation

### Memory & Knowledge
- **Record events** - Save to knowledge graph
- **Query memory** - Search historical data
- **Summarize sessions** - Generate session summaries
- **Export reports** - Comprehensive reporting

### Notifications
- **Console** - Terminal notifications
- **System** - OS-level alerts
- **Toast** - Frontend notifications
- **Email** - SMTP integration
- **Webhooks** - HTTP endpoints
- **Slack** - Team chat integration

### Flow Control
- **Rate limiting** - Prevent spam operations
- **Circuit breakers** - Handle failure cascades
- **Conditional logic** - If-then-else flows
- **Loop control** - Iterative operations

## 📊 Monitoring & Statistics

### System Status
```bash
python mindnext_hooks_v2.py --status
```

Returns comprehensive metrics:
- Event processing statistics
- Rule execution rates  
- Action success/failure rates
- Performance metrics
- Component health status

### Execution Reports
```bash
python mindnext_hooks_v2.py --export-report
```

Generates detailed reports including:
- Rule triggering patterns
- Action execution history
- Performance analysis
- Error tracking
- Usage trends

## 🔧 Extensibility

### Adding Custom Actions

1. Create executor in `flow_engine/actions/`
2. Register in `__init__.py`  
3. Use in rule configurations
4. Define in pipeline workflows

### Core Components Usage

#### Buffer Operations
```python
# Store data
"action.utility/operation=buffer.push&buffer_id=events&data={event_data}"

# Retrieve data
"action.utility/operation=buffer.pop&buffer_id=events"
```

#### Cache Operations  
```python
# Cache results
"action.utility/operation=cache.set&key=result&value={data}&ttl=3600"

# Get cached data
"action.utility/operation=cache.get&key=result"
```

#### AI SDK Operations
```python
# Analyze with AI
"action.utility/operation=aisdk.analyze&text={content}"

# Generate suggestions
"action.utility/operation=aisdk.generate&prompt=Improve code"
```

## 📈 Performance Features

- Built-in caching and buffering
- Async/await processing
- Circuit breakers for resilience
- Rate limiting for stability
- Performance monitoring
- Memory usage optimization

## 🛠️ Development

```bash
# Run comprehensive test
python mindnext_hooks.py --test

# Enable debug mode  
HOOKS_DEBUG=1 python mindnext_hooks.py

# Check system logs
tail -f /root/Dev/mindnext/logs/hooks.log
```

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Add comprehensive tests
4. Update documentation
5. Submit pull request

### Development Setup

```bash
# Clone repository
git clone https://github.com/your-org/mindnext-hooks.git

# Install dependencies
pip install -r requirements.txt

# Run system test
python hooks/mindnext_hooks.py --test
```

## 📄 License

MIT License - Open source and free for all uses.

---

**MindNext Hooks System** - The most comprehensive Claude Code hooks solution. 🚀