# MindNext Hooks System - Three-Layer Architecture

**Version**: 3.0 Three-Layer Architecture  
**Framework**: Event → Rule → Action Flow  
**Created**: 2025-08-09  
**Configuration**: TOML + System Separation  

## 🎯 System Overview

MindNext Hooks System is a comprehensive, modular, and extensible hooks system for Claude Code, featuring a sophisticated three-layer architecture with clean configuration separation. Designed for global use and easy GitHub distribution.

## 🏗️ Three-Layer Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Event Layer   │ ───► │   Rule Layer    │ ───► │ Action Flow     │
│                 │    │                 │    │ Layer           │
│ • Event capture │    │ • Rule matching │    │ • Action exec   │
│ • Standardize   │    │ • Condition eval│    │ • Pipelines     │
│ • Context build │    │ • Priority sort │    │ • Return format │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📁 System Structure

```
hooks/
├── 🚀 mindnext_hooks.py               # Main entry point (Three-Layer)
├── 📄 claude_settings_example.json    # Claude Code settings template
├── 📋 config/                         # Configuration files
│   ├── system.config.toml             # System settings (NEW)
│   ├── rules_config_mapping.toml      # 3D Event→Rule→Action mapping
│   ├── rules_config.json              # Legacy rule definitions  
│   ├── pipelines_config.json          # Action pipelines
│   └── quality_config.json            # Quality settings
├── 🔧 flow_engine/                    # Three-Layer Engine
│   ├── event_layer.py                 # Event processing
│   ├── rule_layer.py                  # Rule matching & TOML loading
│   ├── action_layer.py                # Action execution
│   ├── flow_coordinator.py            # System coordinator
│   ├── system_validator.py            # System validation (MOVED)
│   └── actions/                       # Modular actions
│       ├── action_prompt.py           # Prompt analysis
│       ├── action_ai.py               # AI integration
│       ├── action_quality.py          # Code quality
│       ├── action_memory.py           # Knowledge graph
│       ├── action_notification.py     # Multi-channel alerts
│       ├── action_analysis.py         # Performance metrics
│       ├── action_conditional.py      # Flow control
│       └── action_utility.py          # Core components
└── 🗂️ cleanup/                        # Legacy code archive
```

## ✨ Key Features

### 🆕 **Clean Configuration Architecture**
- **system.config.toml** - Global system settings separated from rules
- **3D Mapping Format** - Event → Rule → Action Flow with return definitions
- **TOML Support** - Comments and better readability
- **Modular Loading** - Auto-load multiple configuration files
- **File-Level Controls** - Enable/disable entire config files

### 🎯 **20+ Modular Action Executors**
- **action.prompt** - Prompt analysis and enhancement
- **action.ai** - AI-powered code analysis and suggestions
- **action.quality** - Comprehensive code quality checks
- **action.memory** - Knowledge graph integration
- **action.notification** - Multi-channel notifications
- **action.analysis** - Performance and usage analytics
- **action.conditional** - Flow control and circuit breakers
- **action.utility** - Core components (Buffer/Cache/AI SDK)

### 🧠 **Enhanced Rule Engine**
- **keyboard rule type** - Array-based keyword matching for Chinese/international
- **Simple conditions** - Tool name matching and boolean expressions
- **Regex patterns** - File type detection and complex matching
- **Priority-based execution** - Configurable rule ordering
- **Cooldown controls** - Rate limiting per rule
- **File pattern filtering** - Include/exclude file patterns

### 🔄 **Structured Return System**
Each rule mapping now includes structured return definitions:
```toml
return = {
    messages = [
        "Found 5 related memory records",    # User feedback messages
        "Memory buffer content ready",
        "Ready to perform memory operations"
    ],
    data = "memory_buffer_ready",            # Return data identifier
    action = "provide_context"               # Return action to execute
}
```

## 🚀 Quick Start

### Setup and Installation

1. **Configure Claude Code hooks** - Copy settings from `claude_settings_example.json` to your `~/.claude/settings.json`
2. **Update paths** - Replace `/path/to/` with actual installation path
3. **Install dependencies** - `pip install -r requirements.txt`
4. **Validate system** - `python flow_engine/system_validator.py --quick`
5. **Test system** - `python mindnext_hooks.py --test`

### Basic Usage

```bash
# Test the system
python mindnext_hooks.py --test

# Validate system configuration
python flow_engine/system_validator.py --quick

# Auto-fix system issues
python flow_engine/system_validator.py --fix

# Get system status  
python mindnext_hooks.py --status

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

### System Configuration (`config/system.config.toml`)

Global system settings separated from rule configurations:

```toml
[config]
enable = true                       # Master enable switch
debug_mode = false                  # Enable debug output

[engine]
max_concurrent_rules = 10           # Maximum concurrent rule processing
enable_rule_chaining = true         # Allow rules to trigger other rules

[rules]
default_priority = 90               # Default rule priority
default_cooldown = 2                # Default cooldown time (seconds)
max_actions_per_trigger = 5         # Max actions per rule trigger

[actions]
parallel_execution = true           # Execute actions in parallel
timeout_seconds = 30                # Action execution timeout

[memory]
enable_buffer = true                # Enable memory buffer system
buffer_size = 100                   # Maximum buffer entries
ttl_seconds = 3600                  # Time to live for buffer entries

[notifications]
enable_console = true               # Enable console notifications
enable_system = false               # Enable system notifications

[security]
validate_actions = true             # Validate action parameters
sandbox_mode = false                # Run actions in sandbox

[performance]
cache_enabled = true                # Enable result caching
metrics_collection = true          # Collect performance metrics
```

### 3D Mapping Configuration (`config/rules_config_mapping.toml`)

Event → Rule → Action Flow 3D mapping table with structured returns:

```toml
[config]
enable = true  # Global enable/disable switch for entire config file

# Chinese keyword trigger rules  
[[mappings]]
event = "UserPromptSubmit"           # Event type
rule = "keyboard"                    # Rule type: keyboard supports keyword arrays
condition = ["記憶", "記錄", "回憶"]    # Trigger keywords (any match will trigger)
enable = true                        # Enable switch for this rule
action_flow = [                      # Action execution flow
    "action.memory/operation=search&limit=5",
    "action.utility/operation=buffer.get&count=5&category=memory", 
    "action.notification/type=console&message=Memory buffer ready"
]
return = {                           # Return definition
    messages = [
        "Found 5 related memory records",
        "Memory buffer content ready", 
        "Ready to perform memory operations"
    ],
    data = "memory_buffer_ready",
    action = "provide_context"
}

# PreToolUse event rules
[[mappings]]
event = "PreToolUse"
rule = "simple"                      # Simple condition matching
condition = "tool_name == 'Read'"   # Tool name matching
enable = true
action_flow = [
    "action.utility/operation=buffer.prepare_read&count=3",
    "action.notification/type=console&message=Read preparation buffer loaded"
]
return = {
    messages = [
        "Read operation buffer prepared",
        "Context analysis ready",
        "Ready for enhanced reading"
    ],
    data = "read_buffer_prepared",
    action = "enhance_reading"
}
```

### Rule Types

1. **keyboard** - Array-based keyword matching (supports Chinese/international)
   ```toml
   condition = ["記憶", "記錄", "回憶"]  # Any keyword match triggers
   ```

2. **simple** - Boolean expressions and tool name matching  
   ```toml
   condition = "tool_name == 'Write'"  # Simple condition
   ```

3. **regex** - Regular expression matching
   ```toml
   condition = "any(re.match(r'.*\\.py$', fp) for fp in file_paths)"  # Python files
   ```

## 🎮 Available Actions

### Quality Assurance
- **Format code** - Auto-format with language-specific tools
- **Lint code** - Static analysis and style checking
- **Security scan** - Detect security vulnerabilities
- **Dependency check** - Package vulnerability scanning
- **Python quality** - Python-specific code checks

### AI Enhancement
- **Code analysis** - AI-powered code review
- **Generate suggestions** - Improvement recommendations  
- **Detect patterns** - Architecture pattern detection
- **Prompt analysis** - User prompt enhancement

### Memory & Knowledge
- **Record events** - Save to knowledge graph
- **Query memory** - Search historical data
- **Load context** - Retrieve session context
- **Session management** - Initialize and cleanup

### Notifications & Feedback
- **Console notifications** - Terminal output
- **System notifications** - OS-level alerts
- **Structured returns** - JSON response format
- **Multi-language messages** - Internationalization support

### Utility & Flow Control
- **Buffer operations** - Event queuing and storage
- **Cache management** - High-performance caching
- **Session initialization** - Setup and teardown
- **Error handling** - Exception management and recovery

## 📊 System Validation & Monitoring

### System Validation
```bash
# Quick system check
python flow_engine/system_validator.py --quick

# Full system validation
python flow_engine/system_validator.py

# Auto-fix issues
python flow_engine/system_validator.py --fix
```

### System Status
```bash
python mindnext_hooks.py --status
```

Returns comprehensive metrics:
- Event processing statistics
- Rule execution rates  
- Action success/failure rates
- Configuration validation status
- System health indicators

## 🔧 Extensibility

### Adding Custom Rules

1. Create new mapping in `config/rules_config_mapping.toml`
2. Define event, rule type, conditions, and action flow
3. Specify structured return format
4. Enable and test the rule

Example:
```toml
[[mappings]]
event = "CustomEvent"
rule = "simple"
condition = "custom_condition == true"
enable = true
action_flow = ["action.custom/operation=process"]
return = {
    messages = ["Custom processing completed"],
    data = "custom_result",
    action = "custom_action"
}
```

### Creating Custom Actions

1. Create executor in `flow_engine/actions/action_custom.py`
2. Inherit from `ActionBase`
3. Implement `execute()` method
4. Register in `actions/__init__.py`
5. Use in rule configurations

## 📈 Performance Features

- **TOML Configuration** - Fast parsing with comment support
- **Separated Concerns** - System settings isolated from rules
- **Modular Loading** - Auto-load multiple config files
- **Built-in Validation** - System integrity checking
- **Structured Returns** - Consistent response format
- **File-Level Controls** - Granular enable/disable

## 🛠️ Development

```bash
# Run comprehensive test
python mindnext_hooks.py --test

# Validate system configuration  
python flow_engine/system_validator.py

# Enable debug mode  
HOOKS_DEBUG=1 python mindnext_hooks.py

# Test specific configuration
python -c "
import toml
config = toml.load('config/rules_config_mapping.toml')
print('Config loaded successfully:', config['config']['enable'])
"
```

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Add comprehensive tests
4. Update TOML configurations
5. Run system validation
6. Submit pull request

### Development Setup

```bash
# Clone repository
git clone https://github.com/your-org/mindnext-hooks.git

# Install dependencies
pip install -r requirements.txt
pip install toml  # For TOML support

# Validate system
python hooks/flow_engine/system_validator.py --quick

# Run system test
python hooks/mindnext_hooks.py --test
```

## 📄 License

MIT License - Open source and free for all uses.

---

**MindNext Hooks System v3.0** - Clean architecture with TOML configuration and system separation. 🚀