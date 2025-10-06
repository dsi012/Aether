#!/usr/bin/env python3
"""
Simplified cFS MCP Server

A lightweight MCP server implementation that doesn't require external MCP libraries.
This version implements the basic MCP protocol for cFS integration.
"""

import asyncio
import json
import socket
import os
import sys
import logging
from typing import Dict, Any, Optional, List
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleMCPServer:
    """Simplified MCP Server for cFS Interface"""
    
    def __init__(self, socket_path: str = "/tmp/cfs_mcp.sock"):
        self.socket_path = socket_path
        self.cfs_socket: Optional[socket.socket] = None
        self.request_id = 1
        self.tools = self._register_tools()
    
    def _register_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register all available MCP tools"""
        return {
            "cfs_send_command": {
                "description": "Send a command to a cFS application",
                "parameters": {
                    "app_name": {"type": "string", "description": "Name of the cFS application"},
                    "command": {"type": "string", "description": "Command name"},
                    "params": {"type": "string", "description": "Command parameters as JSON", "default": ""},
                    "require_confirmation": {"type": "boolean", "description": "Require confirmation", "default": False},
                    "is_critical": {"type": "boolean", "description": "Critical command flag", "default": False}
                },
                "handler": self._handle_send_command
            },
            "cfs_get_telemetry": {
                "description": "Get telemetry data from a cFS application",
                "parameters": {
                    "app_name": {"type": "string", "description": "Application name", "default": "MCP_INTERFACE"}
                },
                "handler": self._handle_get_telemetry
            },
            "cfs_get_system_status": {
                "description": "Get overall cFS system status",
                "parameters": {},
                "handler": self._handle_get_system_status
            },
            "cfs_manage_app": {
                "description": "Manage cFS applications (start, stop, status)",
                "parameters": {
                    "app_name": {"type": "string", "description": "Application name"},
                    "action": {"type": "string", "description": "Action: start, stop, or status"},
                    "require_confirmation": {"type": "boolean", "description": "Require confirmation", "default": True}
                },
                "handler": self._handle_manage_app
            },
            "cfs_list_files": {
                "description": "List files in cFS filesystem",
                "parameters": {
                    "directory": {"type": "string", "description": "Directory path", "default": "/cf"}
                },
                "handler": self._handle_list_files
            },
            "cfs_read_file": {
                "description": "Read file contents from cFS filesystem",
                "parameters": {
                    "file_path": {"type": "string", "description": "Full path to file"}
                },
                "handler": self._handle_read_file
            },
            "cfs_get_event_log": {
                "description": "Get recent events from cFS Event Services",
                "parameters": {},
                "handler": self._handle_get_event_log
            },
            "cfs_emergency_stop": {
                "description": "EMERGENCY STOP - Put spacecraft in safe mode",
                "parameters": {
                    "confirmation": {"type": "string", "description": "Must be 'CONFIRM_EMERGENCY_STOP'", "default": ""}
                },
                "handler": self._handle_emergency_stop
            }
        }
    
    async def _handle_send_command(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle send command request"""
        result = await self._send_cfs_request({
            "id": self._get_request_id(),
            "type": 0,  # MCP_CMD_SEND_COMMAND
            "app_name": params.get("app_name", ""),
            "command": params.get("command", ""),
            "params": params.get("params", ""),
            "require_confirmation": params.get("require_confirmation", False),
            "is_critical": params.get("is_critical", False)
        })
        return {"status": "success", "data": result}
    
    async def _handle_get_telemetry(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get telemetry request"""
        result = await self._send_cfs_request({
            "id": self._get_request_id(),
            "type": 1,  # MCP_CMD_GET_TELEMETRY
            "app_name": params.get("app_name", "MCP_INTERFACE"),
            "command": "",
            "params": ""
        })
        return {"status": "success", "data": result}
    
    async def _handle_get_system_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get system status request"""
        result = await self._send_cfs_request({
            "id": self._get_request_id(),
            "type": 2,  # MCP_CMD_GET_SYSTEM_STATUS
            "app_name": "",
            "command": "",
            "params": ""
        })
        return {"status": "success", "data": result}
    
    async def _handle_manage_app(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle manage app request"""
        result = await self._send_cfs_request({
            "id": self._get_request_id(),
            "type": 3,  # MCP_CMD_MANAGE_APP
            "app_name": params.get("app_name", ""),
            "command": "",
            "params": f'"{params.get("action", "status")}"',
            "require_confirmation": params.get("require_confirmation", True)
        })
        return {"status": "success", "data": result}
    
    async def _handle_list_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle list files request"""
        result = await self._send_cfs_request({
            "id": self._get_request_id(),
            "type": 4,  # MCP_CMD_GET_FILE_LIST
            "app_name": "",
            "command": "",
            "params": f'"{params.get("directory", "/cf")}"'
        })
        return {"status": "success", "data": result}
    
    async def _handle_read_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle read file request"""
        result = await self._send_cfs_request({
            "id": self._get_request_id(),
            "type": 5,  # MCP_CMD_READ_FILE
            "app_name": "",
            "command": "",
            "params": f'"{params.get("file_path", "")}"'
        })
        return {"status": "success", "data": result}
    
    async def _handle_get_event_log(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get event log request"""
        result = await self._send_cfs_request({
            "id": self._get_request_id(),
            "type": 7,  # MCP_CMD_GET_EVENT_LOG
            "app_name": "",
            "command": "",
            "params": ""
        })
        return {"status": "success", "data": result}
    
    async def _handle_emergency_stop(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle emergency stop request"""
        confirmation = params.get("confirmation", "")
        if confirmation != "CONFIRM_EMERGENCY_STOP":
            return {
                "status": "error",
                "error": "Emergency stop requires confirmation='CONFIRM_EMERGENCY_STOP'"
            }
        
        result = await self._send_cfs_request({
            "id": self._get_request_id(),
            "type": 8,  # MCP_CMD_EMERGENCY_STOP
            "app_name": "",
            "command": "",
            "params": "",
            "require_confirmation": True,
            "is_critical": True
        })
        return {"status": "success", "data": result}
    
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
            self.cfs_socket.settimeout(5.0)
            
            # Wait for cFS socket to be available
            max_retries = 10
            for attempt in range(max_retries):
                try:
                    self.cfs_socket.connect(self.socket_path)
                    logger.info(f"Connected to cFS at {self.socket_path}")
                    return True
                except (ConnectionRefusedError, FileNotFoundError):
                    if attempt < max_retries - 1:
                        logger.info(f"cFS socket not ready, retrying... ({attempt + 1}/{max_retries})")
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
    
    async def handle_mcp_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP protocol request"""
        try:
            method = request.get("method", "")
            params = request.get("params", {})
            request_id = request.get("id")
            
            if method == "tools/list":
                # Return list of available tools
                tools_list = []
                for tool_name, tool_info in self.tools.items():
                    tools_list.append({
                        "name": tool_name,
                        "description": tool_info["description"],
                        "inputSchema": {
                            "type": "object",
                            "properties": tool_info["parameters"]
                        }
                    })
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"tools": tools_list}
                }
            
            elif method == "tools/call":
                # Call a specific tool
                tool_name = params.get("name")
                tool_arguments = params.get("arguments", {})
                
                if tool_name not in self.tools:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Unknown tool: {tool_name}"
                        }
                    }
                
                # Execute tool
                tool_handler = self.tools[tool_name]["handler"]
                result = await tool_handler(tool_arguments)
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2)
                            }
                        ]
                    }
                }
            
            elif method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "cfs-mcp-server",
                            "version": "1.0.0"
                        }
                    }
                }
            
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Unknown method: {method}"
                    }
                }
                
        except Exception as e:
            logger.error(f"Error handling MCP request: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    async def run_stdio(self):
        """Run MCP server using stdio transport"""
        logger.info("Starting cFS MCP Server (stdio mode)...")
        
        # Test connection to cFS
        if await self._connect_to_cfs():
            logger.info("Successfully connected to cFS MCP Interface")
        else:
            logger.warning("Could not connect to cFS initially, will retry on first request")
        
        try:
            while True:
                # Read request from stdin
                line = await asyncio.to_thread(sys.stdin.readline)
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                try:
                    request = json.loads(line)
                    response = await self.handle_mcp_request(request)
                    
                    # Write response to stdout
                    print(json.dumps(response))
                    sys.stdout.flush()
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON request: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        }
                    }
                    print(json.dumps(error_response))
                    sys.stdout.flush()
                
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            if self.cfs_socket:
                self.cfs_socket.close()

def main():
    """Main entry point"""
    # Get socket path from environment or use default
    socket_path = os.environ.get('CFS_SOCKET_PATH', '/tmp/cfs_mcp.sock')
    
    # Create and run server
    server = SimpleMCPServer(socket_path)
    
    try:
        asyncio.run(server.run_stdio())
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
