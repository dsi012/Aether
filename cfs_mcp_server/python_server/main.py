#!/usr/bin/env python3
"""
cFS MCP Server - Python Wrapper

This module provides an MCP (Model Context Protocol) server interface
for the Core Flight System (cFS). It communicates with the cFS MCP
Interface Application via Unix domain socket.

Designed for onboard spacecraft deployment with astronaut interaction.
"""

import asyncio
import json
import socket
import os
import sys
import logging
from typing import Dict, Any, Optional, List
import time

# Add the parent directory to the path to import MCP modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from mcp import McpServer, Tool, TextContent
    from mcp.types import TextContent as TextContentType
except ImportError:
    print("MCP library not found. Please install with: pip install mcp")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CFSMCPServer:
    """MCP Server for cFS Interface"""
    
    def __init__(self, socket_path: str = "/tmp/cfs_mcp.sock"):
        self.socket_path = socket_path
        self.cfs_socket: Optional[socket.socket] = None
        self.request_id = 1
        self.server = McpServer("cfs-mcp-server")
        
        # Register MCP tools
        self._register_tools()
    
    def _register_tools(self):
        """Register all MCP tools"""
        
        @self.server.tool("cfs_send_command")
        async def send_command(
            app_name: str,
            command: str,
            params: str = "",
            require_confirmation: bool = False,
            is_critical: bool = False
        ) -> List[TextContentType]:
            """
            Send a command to a cFS application.
            
            Args:
                app_name: Name of the cFS application (e.g., "CFE_ES", "FM")
                command: Command name (e.g., "NOOP", "RESET_COUNTERS")
                params: Command parameters as JSON string (optional)
                require_confirmation: Whether this command requires astronaut confirmation
                is_critical: Whether this is a critical command that affects safety
            
            Returns:
                Command execution result
            """
            try:
                result = await self._send_cfs_request({
                    "id": self._get_request_id(),
                    "type": 0,  # MCP_CMD_SEND_COMMAND
                    "app_name": app_name,
                    "command": command,
                    "params": params,
                    "require_confirmation": require_confirmation,
                    "is_critical": is_critical
                })
                
                return [TextContent(
                    type="text",
                    text=f"Command sent successfully:\n{json.dumps(result, indent=2)}"
                )]
                
            except Exception as e:
                logger.error(f"Error sending command: {e}")
                return [TextContent(
                    type="text", 
                    text=f"Error sending command: {str(e)}"
                )]
        
        @self.server.tool("cfs_get_telemetry")
        async def get_telemetry(
            app_name: str = "MCP_INTERFACE"
        ) -> List[TextContentType]:
            """
            Get telemetry data from a cFS application.
            
            Args:
                app_name: Name of the cFS application to get telemetry from
            
            Returns:
                Telemetry data in JSON format
            """
            try:
                result = await self._send_cfs_request({
                    "id": self._get_request_id(),
                    "type": 1,  # MCP_CMD_GET_TELEMETRY
                    "app_name": app_name,
                    "command": "",
                    "params": ""
                })
                
                return [TextContent(
                    type="text",
                    text=f"Telemetry data:\n{json.dumps(result, indent=2)}"
                )]
                
            except Exception as e:
                logger.error(f"Error getting telemetry: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error getting telemetry: {str(e)}"
                )]
        
        @self.server.tool("cfs_get_system_status")
        async def get_system_status() -> List[TextContentType]:
            """
            Get overall cFS system status and health information.
            
            Returns:
                System status including memory usage, active tasks, and application states
            """
            try:
                result = await self._send_cfs_request({
                    "id": self._get_request_id(),
                    "type": 2,  # MCP_CMD_GET_SYSTEM_STATUS
                    "app_name": "",
                    "command": "",
                    "params": ""
                })
                
                return [TextContent(
                    type="text",
                    text=f"System Status:\n{json.dumps(result, indent=2)}"
                )]
                
            except Exception as e:
                logger.error(f"Error getting system status: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error getting system status: {str(e)}"
                )]
        
        @self.server.tool("cfs_manage_app")
        async def manage_app(
            app_name: str,
            action: str,
            require_confirmation: bool = True
        ) -> List[TextContentType]:
            """
            Manage cFS applications (start, stop, get status).
            
            Args:
                app_name: Name of the cFS application
                action: Action to perform ("start", "stop", "status")
                require_confirmation: Whether to require confirmation for critical actions
            
            Returns:
                Result of the management operation
            """
            try:
                result = await self._send_cfs_request({
                    "id": self._get_request_id(),
                    "type": 3,  # MCP_CMD_MANAGE_APP
                    "app_name": app_name,
                    "command": "",
                    "params": f'"{action}"',
                    "require_confirmation": require_confirmation
                })
                
                return [TextContent(
                    type="text",
                    text=f"App management result:\n{json.dumps(result, indent=2)}"
                )]
                
            except Exception as e:
                logger.error(f"Error managing app: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error managing app: {str(e)}"
                )]
        
        @self.server.tool("cfs_list_files")
        async def list_files(
            directory: str = "/cf"
        ) -> List[TextContentType]:
            """
            List files in a cFS filesystem directory.
            
            Args:
                directory: Directory path to list (default: /cf)
            
            Returns:
                List of files and directories with their properties
            """
            try:
                result = await self._send_cfs_request({
                    "id": self._get_request_id(),
                    "type": 4,  # MCP_CMD_GET_FILE_LIST
                    "app_name": "",
                    "command": "",
                    "params": f'"{directory}"'
                })
                
                return [TextContent(
                    type="text",
                    text=f"File listing:\n{json.dumps(result, indent=2)}"
                )]
                
            except Exception as e:
                logger.error(f"Error listing files: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error listing files: {str(e)}"
                )]
        
        @self.server.tool("cfs_read_file")
        async def read_file(
            file_path: str
        ) -> List[TextContentType]:
            """
            Read contents of a file from the cFS filesystem.
            
            Args:
                file_path: Full path to the file to read
            
            Returns:
                File contents (limited size for safety)
            """
            try:
                result = await self._send_cfs_request({
                    "id": self._get_request_id(),
                    "type": 5,  # MCP_CMD_READ_FILE
                    "app_name": "",
                    "command": "",
                    "params": f'"{file_path}"'
                })
                
                return [TextContent(
                    type="text",
                    text=f"File contents:\n{json.dumps(result, indent=2)}"
                )]
                
            except Exception as e:
                logger.error(f"Error reading file: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error reading file: {str(e)}"
                )]
        
        @self.server.tool("cfs_get_event_log")
        async def get_event_log() -> List[TextContentType]:
            """
            Get recent events from the cFS Event Services log.
            
            Returns:
                Recent system events and messages
            """
            try:
                result = await self._send_cfs_request({
                    "id": self._get_request_id(),
                    "type": 7,  # MCP_CMD_GET_EVENT_LOG
                    "app_name": "",
                    "command": "",
                    "params": ""
                })
                
                return [TextContent(
                    type="text",
                    text=f"Event log:\n{json.dumps(result, indent=2)}"
                )]
                
            except Exception as e:
                logger.error(f"Error getting event log: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error getting event log: {str(e)}"
                )]
        
        @self.server.tool("cfs_emergency_stop")
        async def emergency_stop(
            confirmation: str = ""
        ) -> List[TextContentType]:
            """
            EMERGENCY STOP - Put the spacecraft systems in safe mode.
            
            This is a critical safety command that should only be used in emergencies.
            
            Args:
                confirmation: Must be "CONFIRM_EMERGENCY_STOP" to execute
            
            Returns:
                Emergency stop execution result
            """
            if confirmation != "CONFIRM_EMERGENCY_STOP":
                return [TextContent(
                    type="text",
                    text="EMERGENCY STOP requires confirmation. Set confirmation='CONFIRM_EMERGENCY_STOP' to execute."
                )]
            
            try:
                result = await self._send_cfs_request({
                    "id": self._get_request_id(),
                    "type": 8,  # MCP_CMD_EMERGENCY_STOP
                    "app_name": "",
                    "command": "",
                    "params": "",
                    "require_confirmation": True,
                    "is_critical": True
                })
                
                return [TextContent(
                    type="text",
                    text=f"EMERGENCY STOP executed:\n{json.dumps(result, indent=2)}"
                )]
                
            except Exception as e:
                logger.error(f"Error executing emergency stop: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error executing emergency stop: {str(e)}"
                )]
    
    def _get_request_id(self) -> int:
        """Get next request ID"""
        req_id = self.request_id
        self.request_id += 1
        return req_id
    
    async def _connect_to_cfs(self) -> bool:
        """Connect to cFS MCP Interface Application"""
        try:
            if self.cfs_socket:
                self.cfs_socket.close()
            
            self.cfs_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.cfs_socket.settimeout(5.0)  # 5 second timeout
            
            # Wait for cFS socket to be available
            max_retries = 10
            for attempt in range(max_retries):
                try:
                    self.cfs_socket.connect(self.socket_path)
                    logger.info(f"Connected to cFS at {self.socket_path}")
                    return True
                except (ConnectionRefusedError, FileNotFoundError):
                    if attempt < max_retries - 1:
                        logger.info(f"cFS socket not ready, retrying in 2 seconds... ({attempt + 1}/{max_retries})")
                        await asyncio.sleep(2)
                    else:
                        logger.error(f"Failed to connect to cFS after {max_retries} attempts")
                        return False
            
        except Exception as e:
            logger.error(f"Error connecting to cFS: {e}")
            return False
        
        return False
    
    async def _send_cfs_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send request to cFS and get response"""
        if not self.cfs_socket:
            if not await self._connect_to_cfs():
                raise Exception("Cannot connect to cFS MCP Interface")
        
        try:
            # Send request
            request_json = json.dumps(request)
            self.cfs_socket.send(request_json.encode('utf-8'))
            
            # Receive response
            response_data = self.cfs_socket.recv(4096)
            if not response_data:
                raise Exception("No response from cFS")
            
            response = json.loads(response_data.decode('utf-8'))
            
            if response.get('status', -1) != 0:
                error_msg = response.get('error', 'Unknown error')
                raise Exception(f"cFS error: {error_msg}")
            
            return response.get('result', {})
            
        except socket.timeout:
            logger.error("Timeout waiting for cFS response")
            raise Exception("Timeout waiting for cFS response")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from cFS: {e}")
            raise Exception("Invalid response from cFS")
        except Exception as e:
            logger.error(f"Error communicating with cFS: {e}")
            # Try to reconnect on next request
            if self.cfs_socket:
                self.cfs_socket.close()
                self.cfs_socket = None
            raise
    
    async def run(self):
        """Run the MCP server"""
        try:
            logger.info("Starting cFS MCP Server...")
            
            # Test connection to cFS
            if await self._connect_to_cfs():
                logger.info("Successfully connected to cFS MCP Interface")
            else:
                logger.warning("Could not connect to cFS initially, will retry on first request")
            
            # Run the MCP server
            import mcp.server.stdio
            async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
                await self.server.run(read_stream, write_stream, self.server.create_initialization_options())
                
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise
        finally:
            if self.cfs_socket:
                self.cfs_socket.close()

def main():
    """Main entry point"""
    # Get socket path from environment or use default
    socket_path = os.environ.get('CFS_SOCKET_PATH', '/tmp/cfs_mcp.sock')
    
    # Create and run server
    server = CFSMCPServer(socket_path)
    
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
