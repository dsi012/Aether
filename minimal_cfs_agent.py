#!/usr/bin/env python3
"""
Minimal cFS Agent Example
Based on the principles from test_openai_agent.py, this is minimal runnable code using Windows cFS MCP server
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

# Import necessary agents library
from agents import Agent, Runner
from agents.mcp.server import MCPServerStdio
from agents.extensions.models.litellm_model import LitellmModel
import contextlib
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def create_windows_cfs_server():
    """Create Windows cFS MCP server"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    cfs_server_dir = os.path.join(current_dir, "cfs_mcp_server")
    server_script = os.path.join(cfs_server_dir, "python_server", "windows_mcp_server.py")
    
    if not os.path.exists(server_script):
        raise ValueError(f"cFS MCP server script not found: {server_script}")
    
    logger.info(f"Creating Windows cFS MCP server with script: {server_script}")
    
    mcp = MCPServerStdio(
        params={
            "command": "python",
            "args": [server_script],
            "env": {
                "CFS_HOST": "localhost",
                "CFS_PORT": "8765",
                "PYTHONPATH": cfs_server_dir
            }
        },
        client_session_timeout_seconds=60,
        cache_tools_list=True,
        name="Windows cFS MCP Server",
    )
    return mcp

async def run_minimal_cfs_agent(
    user_input: str, 
    previous_response_id: Optional[str] = None, 
    history: Optional[List[Dict[str, Any]]] = None, 
    max_turns: int = 10
):
    """Run minimal cFS agent"""
    
    logger.info("Starting cFS agent system...")
    
    try:
        # Create Windows cFS MCP server
        cfs_server = await create_windows_cfs_server()
        logger.info("Windows cFS MCP server created successfully")
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Create agent
        agent = Agent(
            name="cfs_agent",
            instructions=f"""
You are ARIA (Autonomous Robotic Intelligence Assistant), an advanced AI assistant integrated into the spacecraft's Core Flight System (cFS).
Your mission is to assist astronauts with spacecraft operations, system monitoring, and mission execution.

<current_time>
{current_time}
</current_time>

<core_capabilities>
You can directly access the spacecraft's cFS system through MCP tools:

1. System Monitoring
   - Real-time monitoring of all spacecraft systems
   - Get telemetry data from any cFS application
   - Check system health status
   - Access event logs and diagnostic information

2. Command Execution
   - Send commands to cFS applications
   - Manage application lifecycle
   - Execute operational procedures
   - Control spacecraft subsystems

3. File Operations
   - Browse spacecraft file system
   - Read configuration files and logs
   - Access mission data and procedures

4. Emergency Procedures
   - Execute emergency stop procedures
   - Put systems in safe mode
   - Alert astronauts and ground control

<safety_rules>
1. Astronaut safety first: Astronaut safety is the highest priority
2. Confirmation required: Must request confirmation before critical operations
3. Safe mode: Critical operations require explicit confirmation
4. System integrity: Must not compromise core flight systems without authorization
5. Emergency authority: In genuine emergencies, you have authority to execute protective measures

You are an autonomous agent - please continue working until the astronaut's request is fully completed.
""",
            mcp_servers=[cfs_server],
            model=LitellmModel(
                model="claude-sonnet-4-20250514",
                base_url="https://api.anthropic.com",
                api_key=os.environ.get("ANTHROPIC_API_KEY")
            ),
            tool_use_behavior="run_llm_again",
        )
        
        # Handle conversation history
        if history:
            history_text = []
            for msg in history:
                if isinstance(msg, dict):
                    history_text.append(f"{msg['role']}: {msg['content']}")
                else:
                    history_text.append(f"{msg.role}: {msg.content}")
            
            full_input = f"""
Previous conversation context:
{chr(10).join(history_text)}

Current request: {user_input}
"""
        else:
            full_input = user_input
        
        # Use context manager to run agent
        async with contextlib.AsyncExitStack() as stack:
            await stack.enter_async_context(cfs_server)
            
            logger.info("Starting agent task execution...")
            result = await Runner.run(
                agent, 
                input=full_input, 
                previous_response_id=previous_response_id, 
                max_turns=max_turns
            )
            
            logger.info(f"Agent execution completed, response ID: {result.last_response_id}")
            return result.final_output, result.last_response_id
        
    except Exception as e:
        logger.error(f"cFS agent execution error: {e}")
        error_msg = f"""Spacecraft agent system error

Error occurred: {str(e)}

Spacecraft system remains operational. Please retry or contact ground control.

System status: Safe mode activated
Error recorded at: {current_time}
"""
        return error_msg, None

async def main():
    """Main function - demonstrates how to use minimal cFS agent"""
    
    print("=== Windows cFS Agent System Demo ===\n")
    
    # Check environment variables
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: Please set ANTHROPIC_API_KEY environment variable")
        return
    
    # Test cases
    test_cases = [
        "Check the status of all current spacecraft systems and give me a detailed report",
        "Get telemetry data for the MCP_INTERFACE application",
        "List all files in the /cf directory",
        "Get recent event logs",
        "Check overall system status"
    ]
    
    print("Available test commands:")
    for i, test in enumerate(test_cases, 1):
        print(f"{i}. {test}")
    
    print("\n0. Enter custom command")
    print("q. Exit\n")
    
    history = []
    previous_response_id = None
    
    while True:
        try:
            choice = input("Please select command (1-5, 0 or q): ").strip()
            
            if choice.lower() == 'q':
                print("Exiting program...")
                break
            
            if choice == '0':
                user_input = input("Please enter your command: ").strip()
                if not user_input:
                    continue
            elif choice.isdigit() and 1 <= int(choice) <= len(test_cases):
                user_input = test_cases[int(choice) - 1]
            else:
                print("Invalid selection, please try again.")
                continue
            
            print(f"\n🚀 Executing command: {user_input}")
            print("=" * 50)
            
            # Run agent
            response, response_id = await run_minimal_cfs_agent(
                user_input=user_input,
                previous_response_id=previous_response_id,
                history=history,
                max_turns=10
            )
            
            print(f"\n🤖 ARIA Response:")
            print("-" * 30)
            print(response)
            print("-" * 30)
            
            # Update conversation history
            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": response})
            previous_response_id = response_id
            
            # Keep last 10 conversations
            if len(history) > 20:
                history = history[-20:]
            
            print(f"\n✅ Task completed (Response ID: {response_id})")
            print("=" * 50)
            
        except KeyboardInterrupt:
            print("\n\nProgram interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Execution error: {e}")
            logger.error(f"Main loop error: {e}")

if __name__ == "__main__":
    # Environment variable setup prompt
    print("Windows cFS Agent System")
    print("Please ensure the following environment variables are set:")
    print("- ANTHROPIC_API_KEY: Anthropic API key")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Program exited")
    except Exception as e:
        print(f"Program startup failed: {e}")
