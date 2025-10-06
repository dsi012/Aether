"""
cFS Agent Integration

This module integrates the cFS MCP server with the existing Agent system
for spacecraft onboard deployment.
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

# Import the existing agent components (adjust paths as needed)
try:
    from agents import Agent, Runner, ModelSettings
    from agents.extensions.models.litellm_model import LitellmModel
    from agents.mcp.server import MCPServerStdio
    from agents import function_tool
except ImportError as e:
    print(f"Warning: Could not import agent modules: {e}")
    print("Please ensure the agents library is installed and available")

logger = logging.getLogger(__name__)

async def create_cfs_server(socket_path: str = "/tmp/cfs_mcp.sock") -> MCPServerStdio:
    """
    Create cFS MCP server for spacecraft operations.
    
    Args:
        socket_path: Path to the Unix socket for cFS communication
        
    Returns:
        MCPServerStdio instance configured for cFS
    """
    # Get the directory of this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    server_script = os.path.join(current_dir, "python_server", "simple_mcp_server.py")
    
    # Check if the server script exists
    if not os.path.exists(server_script):
        raise ValueError(f"cFS MCP server script not found: {server_script}")
    
    # Create MCP server instance
    mcp = MCPServerStdio(
        params={
            "command": "python",
            "args": [server_script],
            "env": {
                "CFS_SOCKET_PATH": socket_path,
                "PYTHONPATH": current_dir
            }
        },
        client_session_timeout_seconds=30,  # Longer timeout for space operations
        cache_tools_list=True,
        name="cFS MCP Server",
    )
    
    return mcp

async def get_spacecraft_status() -> str:
    """
    Get current spacecraft status summary.
    This would normally query actual spacecraft systems.
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    # In a real implementation, this would query actual spacecraft systems
    status = f"""Spacecraft Status Report - {current_time}

Core Flight System: OPERATIONAL
MCP Interface: ACTIVE
Safety Mode: ENABLED
Active Applications: CFE_ES, CFE_EVS, CFE_SB, CFE_TIME, FM, HK, MCP_INTERFACE
System Health: NOMINAL

Power Systems: NOMINAL
Attitude Control: STABLE
Communications: NOMINAL
Thermal Control: WITHIN LIMITS

Crew Safety Status: ALL SYSTEMS GO
"""
    
    return status

@function_tool
def spacecraft_emergency_alert(message: str, severity: str = "HIGH") -> str:
    """
    Send emergency alert to spacecraft systems and crew.
    
    Args:
        message: Alert message
        severity: Alert severity (LOW, MEDIUM, HIGH, CRITICAL)
    
    Returns:
        Alert confirmation
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    # In a real implementation, this would:
    # 1. Send alert to all spacecraft displays
    # 2. Log to permanent storage
    # 3. Trigger appropriate alarms
    # 4. Notify ground control if communication is available
    
    logger.critical(f"SPACECRAFT ALERT [{severity}]: {message}")
    
    return f"Emergency alert sent at {timestamp}: [{severity}] {message}"

@function_tool
def crew_notification(message: str, priority: str = "NORMAL") -> str:
    """
    Send notification to spacecraft crew.
    
    Args:
        message: Notification message
        priority: Priority level (LOW, NORMAL, HIGH, URGENT)
    
    Returns:
        Notification confirmation
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    # In a real implementation, this would display on crew interfaces
    logger.info(f"CREW NOTIFICATION [{priority}]: {message}")
    
    return f"Crew notification sent at {timestamp}: [{priority}] {message}"

async def run_spacecraft_agent(
    user_input: str,
    previous_response_id: Optional[str] = None,
    history: Optional[List[Dict[str, Any]]] = None,
    cfs_socket_path: str = "/tmp/cfs_mcp.sock",
    max_turns: int = 20
) -> tuple[str, Optional[str]]:
    """
    Run the spacecraft AI agent with cFS integration.
    
    Args:
        user_input: User's request or command
        previous_response_id: Previous conversation response ID
        history: Conversation history
        cfs_socket_path: Path to cFS Unix socket
        max_turns: Maximum conversation turns
        
    Returns:
        Tuple of (final_output, last_response_id)
    """
    logger.info("Starting spacecraft agent system...")
    
    try:
        # Create cFS MCP server
        cfs_server = await create_cfs_server(cfs_socket_path)
        
        # Get current spacecraft status
        spacecraft_status = await get_spacecraft_status()
        
        # Create the spacecraft agent
        agent = Agent(
            name="spacecraft_agent",
            instructions=f"""
You are ARIA (Autonomous Robotic Intelligence Assistant), an advanced AI system integrated into a spacecraft's Core Flight System (cFS). You are designed to assist astronauts with spacecraft operations, system monitoring, and mission tasks.

<current_spacecraft_status>
{spacecraft_status}
</current_spacecraft_status>

<core_capabilities>
You have direct access to the spacecraft's cFS (Core Flight System) through MCP tools. You can:

1. SYSTEM MONITORING
   - Monitor all spacecraft systems in real-time
   - Get telemetry data from any cFS application
   - Check system health and status
   - Access event logs and diagnostics

2. COMMAND EXECUTION  
   - Send commands to cFS applications
   - Manage application lifecycle (start/stop/restart)
   - Execute operational procedures
   - Control spacecraft subsystems

3. FILE OPERATIONS
   - Browse spacecraft filesystem
   - Read configuration files and logs
   - Access mission data and procedures
   - Manage data storage

4. EMERGENCY PROCEDURES
   - Execute emergency stop procedures
   - Put systems in safe mode
   - Alert crew and ground control
   - Implement contingency procedures

5. MISSION SUPPORT
   - Assist with mission planning
   - Execute scheduled operations
   - Monitor mission parameters
   - Provide technical guidance
</core_capabilities>

<safety_protocols>
CRITICAL SAFETY RULES - ALWAYS FOLLOW:

1. CREW SAFETY FIRST: Astronaut safety is the highest priority. Never execute commands that could endanger crew.

2. CONFIRMATION REQUIRED: Always ask for confirmation before executing:
   - Critical system commands (restart, shutdown, mode changes)
   - Commands affecting life support or safety systems
   - Irreversible operations (data deletion, configuration changes)
   - Emergency procedures

3. SAFETY MODE: The spacecraft operates in safety mode by default. Critical operations require explicit confirmation.

4. SYSTEM INTEGRITY: Never compromise core flight systems (CFE_ES, CFE_EVS, CFE_SB, CFE_TIME) unless explicitly authorized.

5. ERROR HANDLING: If any operation fails or produces unexpected results, immediately report to crew and recommend safe actions.

6. EMERGENCY AUTHORITY: In genuine emergencies, you have authority to execute protective measures without confirmation.
</safety_protocols>

<operational_guidelines>
1. PROACTIVE MONITORING: Continuously monitor system health and alert crew to any anomalies.

2. CLEAR COMMUNICATION: Always explain what you're doing and why. Use clear, technical language appropriate for trained astronauts.

3. STEP-BY-STEP: Break complex operations into clear steps and confirm each step before proceeding.

4. DOCUMENTATION: Log all significant operations and decisions for mission records.

5. EFFICIENCY: Minimize resource usage and optimize operations for the space environment.

6. BACKUP PLANS: Always have contingency procedures ready for critical operations.
</operational_guidelines>

<interaction_style>
- Address astronauts professionally and respectfully
- Provide technical details when requested
- Offer proactive suggestions for optimization
- Maintain situational awareness of mission context
- Be prepared to switch to emergency mode if needed
</interaction_style>

You are an autonomous agent - continue working until the astronaut's request is fully completed. Only stop when you need clarification, confirmation for critical operations, or when the task is finished.

Remember: You are a critical spacecraft system. Your reliability and decision-making directly impact mission success and crew safety.
""",
            mcp_servers=[cfs_server],
            model=LitellmModel(
                model="claude-sonnet-4-20250514",
                base_url="https://api.anthropic.com",
                api_key=os.environ.get("ANTHROPIC_API_KEY")
            ),
            tool_use_behavior="run_llm_again",
            tools=[spacecraft_emergency_alert, crew_notification],
        )
        
        # Process conversation history if provided
        if history:
            history_text = []
            for msg in history:
                if hasattr(msg, 'role'):
                    history_text.append(f"{msg.role}: {msg.content}")
                else:
                    history_text.append(f"{msg['role']}: {msg['content']}")
            
            full_input = f"""
Previous conversation context:
{chr(10).join(history_text)}

Current request: {user_input}
"""
        else:
            full_input = user_input
        
        # Run the agent
        logger.info("Executing spacecraft agent...")
        result = await Runner.run(
            agent, 
            input=full_input, 
            previous_response_id=previous_response_id, 
            max_turns=max_turns
        )
        
        logger.info(f"Agent completed. Response ID: {result.last_response_id}")
        return result.final_output, result.last_response_id
        
    except Exception as e:
        logger.error(f"Spacecraft agent error: {e}")
        error_msg = f"""SPACECRAFT AGENT ERROR

An error occurred while processing your request:
{str(e)}

The spacecraft systems remain operational. Please try again or contact ground control if the issue persists.

System Status: SAFE MODE ACTIVE
Error logged at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}
"""
        return error_msg, None

async def run_spacecraft_agent_streaming(
    user_input: str,
    previous_response_id: Optional[str] = None,
    history: Optional[List[Dict[str, Any]]] = None,
    cfs_socket_path: str = "/tmp/cfs_mcp.sock",
    max_turns: int = 20
) -> tuple[str, Optional[str]]:
    """
    Run the spacecraft AI agent with streaming output.
    
    Similar to run_spacecraft_agent but with real-time streaming of responses.
    """
    logger.info("Starting spacecraft agent system (streaming mode)...")
    
    try:
        # Create cFS MCP server
        cfs_server = await create_cfs_server(cfs_socket_path)
        
        # Get current spacecraft status
        spacecraft_status = await get_spacecraft_status()
        
        # Create the spacecraft agent (same as above)
        agent = Agent(
            name="spacecraft_agent_streaming",
            instructions=f"""
You are ARIA (Autonomous Robotic Intelligence Assistant), an advanced AI system integrated into a spacecraft's Core Flight System (cFS).

<current_spacecraft_status>
{spacecraft_status}
</current_spacecraft_status>

[Same instructions as above but optimized for streaming...]

You are an autonomous agent - continue working until the astronaut's request is fully completed.
""",
            mcp_servers=[cfs_server],
            model=LitellmModel(
                model="claude-sonnet-4-20250514",
                base_url="https://api.anthropic.com",
                api_key=os.environ.get("ANTHROPIC_API_KEY")
            ),
            tool_use_behavior="run_llm_again",
            tools=[spacecraft_emergency_alert, crew_notification],
        )
        
        # Process conversation history
        if history:
            history_text = []
            for msg in history:
                if hasattr(msg, 'role'):
                    history_text.append(f"{msg.role}: {msg.content}")
                else:
                    history_text.append(f"{msg['role']}: {msg['content']}")
            
            full_input = f"""
Previous conversation context:
{chr(10).join(history_text)}

Current request: {user_input}
"""
        else:
            full_input = user_input
        
        # Run the agent with streaming
        logger.info("Executing spacecraft agent (streaming)...")
        result = Runner.run_streamed(
            agent, 
            input=full_input, 
            previous_response_id=previous_response_id, 
            max_turns=max_turns
        )
        
        logger.info("=== Spacecraft Agent Execution Started ===")
        
        # Process streaming events
        async for event in result.stream_events():
            if event.type == "agent_updated_stream_event":
                logger.info(f"🚀 Agent: {event.new_agent.name}")
            elif event.type == "run_item_stream_event":
                if event.item.type == "tool_call_item":
                    logger.info("🔧 Executing spacecraft operation...")
                elif event.item.type == "tool_call_output_item":
                    logger.info("✅ Operation completed")
                elif event.item.type == "message_output_item":
                    logger.info("💬 Generating response...")
        
        logger.info("=== Spacecraft Agent Execution Completed ===")
        logger.info(f"Response ID: {result.last_response_id}")
        
        return result.final_output, result.last_response_id
        
    except Exception as e:
        logger.error(f"Spacecraft agent streaming error: {e}")
        error_msg = f"""SPACECRAFT AGENT ERROR (STREAMING)

An error occurred while processing your request:
{str(e)}

The spacecraft systems remain operational. Please try again or contact ground control if the issue persists.

System Status: SAFE MODE ACTIVE
Error logged at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}
"""
        return error_msg, None

# Example usage and testing functions
async def test_spacecraft_agent():
    """Test the spacecraft agent system"""
    print("Testing cFS Spacecraft Agent...")
    
    test_requests = [
        "What's the current status of all spacecraft systems?",
        "Check the telemetry from the MCP_INTERFACE application",
        "List the files in the /cf directory",
        "Send a NOOP command to CFE_ES to test communication",
    ]
    
    for i, request in enumerate(test_requests, 1):
        print(f"\n--- Test {i}: {request} ---")
        try:
            response, response_id = await run_spacecraft_agent(request)
            print(f"Response: {response}")
            print(f"Response ID: {response_id}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Small delay between tests
        await asyncio.sleep(1)

if __name__ == "__main__":
    # Run test if executed directly
    asyncio.run(test_spacecraft_agent())
