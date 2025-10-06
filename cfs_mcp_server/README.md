# cFS MCP Server

A Model Context Protocol (MCP) server for NASA's Core Flight System (cFS), enabling AI agents to interact with spacecraft flight software systems.

## Overview

This project provides a bridge between AI agents and cFS (Core Flight System), allowing astronauts to use natural language to monitor, control, and manage spacecraft systems through an AI assistant.

### Key Features

- **Direct cFS Integration**: Native cFS application that communicates through the software bus
- **MCP Protocol Support**: Standard MCP interface for AI agent integration
- **Safety-First Design**: Multiple layers of safety checks and confirmation requirements
- **Real-time Operations**: Low-latency communication suitable for spacecraft operations
- **Comprehensive Monitoring**: Access to telemetry, events, and system status
- **File System Access**: Safe file operations within allowed directories
- **Emergency Procedures**: Built-in emergency stop and safe mode capabilities

## Architecture

```
┌─────────────────────────────────────────┐
│           AI Agent (ARIA)               │
└─────────────┬───────────────────────────┘
              │ MCP Protocol
┌─────────────▼───────────────────────────┐
│         Python MCP Server               │
│  ┌─────────────┬─────────────────────┐  │
│  │ MCP Handler │  JSON-RPC Parser    │  │
│  └─────────────┴─────────────────────┘  │
└─────────────┬───────────────────────────┘
              │ Unix Socket
┌─────────────▼───────────────────────────┐
│         cFS MCP Interface App           │
│  ┌─────────────┬─────────────────────┐  │
│  │ Socket Srv  │  Safety Checks      │  │
│  └─────────────┴─────────────────────┘  │
└─────────────┬───────────────────────────┘
              │ cFS Software Bus
┌─────────────▼───────────────────────────┐
│            cFS Core System              │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐      │
│  │ ES  │ │ EVS │ │ FM  │ │ HK  │ ... │
│  └─────┘ └─────┘ └─────┘ └─────┘      │
└─────────────────────────────────────────┘
```

## Components

### 1. cFS MCP Interface Application (`cfs_app/`)

A native cFS application written in C that:
- Provides Unix domain socket server for external communication
- Implements safety checks and validation
- Translates MCP requests to cFS commands
- Manages client connections and request routing

### 2. Python MCP Server (`python_server/`)

A Python wrapper that:
- Implements the MCP protocol specification
- Handles JSON-RPC communication
- Provides tool definitions for AI agents
- Manages connection to the cFS application

### 3. Agent Integration (`cfs_agent_integration.py`)

Integration layer that:
- Creates the spacecraft AI agent (ARIA)
- Configures safety protocols and instructions
- Manages conversation flow and context
- Provides emergency procedures and alerts

## Installation

### Prerequisites

- cFS development environment
- Python 3.8+
- CMake 3.5+
- GCC compiler
- cJSON library

### Build cFS Application

1. Copy the cFS application to your cFS apps directory:
```bash
cp -r cfs_mcp_server/cfs_app /path/to/cfs/apps/mcp_interface
```

2. Add to your cFS build configuration:
```cmake
# In targets.cmake
list(APPEND MISSION_GLOBAL_APPLIST mcp_interface)
```

3. Build cFS:
```bash
make prep
make
make install
```

### Install Python Dependencies

```bash
cd cfs_mcp_server/python_server
pip install -r requirements.txt
```

## Usage

### 1. Start cFS System

```bash
cd /path/to/cfs/build/exe/cpu1
./core-cpu1
```

### 2. Test MCP Server

```bash
cd cfs_mcp_server
python python_server/simple_mcp_server.py
```

### 3. Run Spacecraft Agent

```python
from cfs_agent_integration import run_spacecraft_agent

# Example usage
response, response_id = await run_spacecraft_agent(
    "Check the status of all spacecraft systems"
)
print(response)
```

## Available MCP Tools

### System Monitoring
- `cfs_get_system_status()` - Get overall system health
- `cfs_get_telemetry(app_name)` - Get application telemetry
- `cfs_get_event_log()` - Get recent system events

### Command Execution
- `cfs_send_command(app_name, command, params)` - Send commands to applications
- `cfs_manage_app(app_name, action)` - Start/stop/status applications

### File Operations
- `cfs_list_files(directory)` - List directory contents
- `cfs_read_file(file_path)` - Read file contents (limited size)

### Emergency Procedures
- `cfs_emergency_stop(confirmation)` - Put spacecraft in safe mode

## Safety Features

### Multi-Layer Safety System

1. **Command Validation**: All commands are validated before execution
2. **Critical Command Detection**: Dangerous commands require confirmation
3. **Rate Limiting**: Critical commands are rate-limited
4. **Safe Mode**: System operates in safe mode by default
5. **File System Protection**: Only allowed directories are accessible
6. **Emergency Stop**: Immediate safe mode activation capability

### Safety Configuration

Critical commands and applications are defined in `config/cfs_config.json`:

```json
{
  "safety_settings": {
    "critical_commands": ["RESTART", "STOP", "DELETE"],
    "critical_apps": ["CFE_ES", "CFE_EVS", "CFE_SB"],
    "require_confirmation": true,
    "allowed_file_paths": ["/cf", "/ram", "/tmp"]
  }
}
```

## Agent Instructions

The AI agent (ARIA) is configured with comprehensive instructions for spacecraft operations:

- **Safety Protocols**: Crew safety is the highest priority
- **Confirmation Requirements**: Critical operations require explicit approval
- **System Knowledge**: Understanding of cFS architecture and operations
- **Emergency Authority**: Ability to execute protective measures in emergencies
- **Professional Communication**: Appropriate interaction style for astronauts

## Example Interactions

### System Status Check
```
Astronaut: "ARIA, give me a status report on all spacecraft systems"

ARIA: "Checking all spacecraft systems now...

*Executes cfs_get_system_status()*

Current Spacecraft Status:
- Core Flight System: OPERATIONAL
- All critical applications running normally
- System health: NOMINAL
- Power systems: STABLE
- No active alerts or warnings

All systems are functioning within normal parameters. Is there any specific system you'd like me to examine in more detail?"
```

### Emergency Situation
```
Astronaut: "ARIA, we have a power anomaly, put the spacecraft in safe mode immediately"

ARIA: "EMERGENCY DETECTED - Executing immediate safe mode procedures...

*Executes cfs_emergency_stop(confirmation="CONFIRM_EMERGENCY_STOP")*

SAFE MODE ACTIVATED
- All non-essential systems stopped
- Power consumption minimized  
- Critical life support maintained
- Ground control alerted
- Event logged for analysis

The spacecraft is now in safe mode. All crew safety systems remain operational. Please advise on next steps or contact ground control for further guidance."
```

## Development

### Adding New Commands

1. Update the cFS application command handlers in `mcp_command_handlers.c`
2. Add command definitions to `config/cfs_config.json`
3. Update Python MCP tools in `simple_mcp_server.py`
4. Test thoroughly with safety protocols

### Extending Safety Checks

1. Modify safety validation in `mcp_safety_utils.c`
2. Update safety configuration in `cfs_config.json`
3. Add appropriate logging and alerts
4. Verify emergency procedures still function

## Testing

### Unit Tests
```bash
cd cfs_mcp_server
python -m pytest tests/
```

### Integration Tests
```bash
# Start cFS in test mode
./test_cfs_integration.sh

# Run agent tests
python test_spacecraft_agent.py
```

### Safety Tests
```bash
# Test emergency procedures
python test_emergency_procedures.py

# Test safety validations
python test_safety_checks.py
```

## Troubleshooting

### Common Issues

1. **Socket Connection Failed**
   - Ensure cFS MCP Interface app is running
   - Check socket path permissions
   - Verify no other process is using the socket

2. **Command Execution Failed**
   - Check cFS application is loaded and running
   - Verify command parameters are correct
   - Review safety settings and confirmations

3. **Agent Not Responding**
   - Check Python MCP server logs
   - Verify API keys are set correctly
   - Ensure network connectivity for model access

### Logs and Debugging

- cFS Events: Check cFS event messages for application status
- Python Logs: Enable debug mode in MCP server
- Agent Logs: Review agent execution logs for errors
- Safety Logs: Monitor safety system alerts and blocks

## Contributing

This is a critical spacecraft system. All contributions must:

1. Pass comprehensive safety reviews
2. Include thorough testing
3. Follow NASA coding standards
4. Be reviewed by flight software experts
5. Include documentation updates

## License

This project is released under the Apache 2.0 license, consistent with NASA's cFS framework.

## Contact

For questions about spacecraft integration or safety concerns, contact the cFS development team.

---

**⚠️ SAFETY WARNING**: This system is designed for spacecraft operations. All safety protocols must be followed. Never bypass safety checks in operational environments.
