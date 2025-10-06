#!/usr/bin/env python3
"""
Windows Compatible cFS MCP Server

A Windows-compatible version of the cFS MCP server that uses TCP sockets
instead of Unix domain sockets for communication.
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

class WindowsCFSMCPServer:
    """Windows-compatible MCP Server for cFS Interface"""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
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
        # For Windows demo, return mock data
        return {
            "status": "success", 
            "data": {
                "command_sent": True,
                "app": params.get("app_name", ""),
                "command": params.get("command", ""),
                "message": f"Mock command sent to {params.get('app_name', 'unknown')}"
            }
        }
    
    async def _handle_get_telemetry(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get telemetry request"""
        app_name = params.get("app_name", "MCP_INTERFACE")
        return {
            "status": "success",
            "data": {
                "app_name": app_name,
                "timestamp": int(time.time()),
                "telemetry": {
                    "cmd_counter": 42,
                    "err_counter": 0,
                    "active_clients": 1,
                    "system_status": "OPERATIONAL",
                    "health": "NOMINAL"
                }
            }
        }
    
    async def _handle_get_system_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get system status request"""
        return {
            "status": "success",
            "data": {
                "system_status": {
                    "timestamp": int(time.time()),
                    "cfs_version": "cFE 7.0 (Windows Demo)",
                    "applications": {
                        "CFE_ES": "RUNNING",
                        "CFE_EVS": "RUNNING", 
                        "CFE_SB": "RUNNING",
                        "FM": "RUNNING",
                        "HK": "RUNNING",
                        "MCP_INTERFACE": "RUNNING"
                    },
                    "memory_usage": "45%",
                    "cpu_usage": "12%",
                    "system_health": "NOMINAL"
                }
            }
        }
    
    async def _handle_manage_app(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle manage app request"""
        app_name = params.get("app_name", "")
        action = params.get("action", "status")
        
        return {
            "status": "success",
            "data": {
                "app_management": {
                    "app": app_name,
                    "action": action,
                    "status": "success",
                    "message": f"Mock {action} operation on {app_name}"
                }
            }
        }
    
    async def _handle_list_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle list files request"""
        directory = params.get("directory", "/cf")
        return {
            "status": "success",
            "data": {
                "directory": directory,
                "files": [
                    {"name": "test_file.txt", "size": 1024, "type": "file"},
                    {"name": "config", "size": 0, "type": "directory"},
                    {"name": "logs", "size": 0, "type": "directory"},
                    {"name": "data.bin", "size": 2048, "type": "file"}
                ]
            }
        }
    
    async def _handle_read_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle read file request"""
        file_path = params.get("file_path", "")
        return {
            "status": "success",
            "data": {
                "file_path": file_path,
                "size": 256,
                "content": f"Mock file content for {file_path}\nThis is a test file.\nTimestamp: {time.time()}"
            }
        }
    
    async def _handle_get_event_log(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get event log request"""
        return {
            "status": "success",
            "data": {
                "event_log": {
                    "timestamp": int(time.time()),
                    "recent_events": [
                        {
                            "id": 1,
                            "app": "MCP_INTERFACE",
                            "type": "INFO",
                            "time": int(time.time()) - 60,
                            "message": "MCP Interface started"
                        },
                        {
                            "id": 2,
                            "app": "CFE_ES",
                            "type": "INFO", 
                            "time": int(time.time()) - 30,
                            "message": "Application status nominal"
                        }
                    ]
                }
            }
        }
    
    async def _handle_emergency_stop(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle emergency stop request"""
        confirmation = params.get("confirmation", "")
        if confirmation != "CONFIRM_EMERGENCY_STOP":
            return {
                "status": "error",
                "error": "Emergency stop requires confirmation='CONFIRM_EMERGENCY_STOP'"
            }
        
        return {
            "status": "success",
            "data": {
                "emergency_stop": {
                    "timestamp": int(time.time()),
                    "status": "executed",
                    "actions": ["safe_mode_enabled", "non_essential_apps_stopped"],
                    "message": "Mock emergency stop executed"
                }
            }
        }
    
    def _get_request_id(self) -> int:
        """Get next request ID"""
        req_id = self.request_id
        self.request_id += 1
        return req_id
    
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
                            "name": "cfs-mcp-server-windows",
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
        logger.info("Starting Windows cFS MCP Server (stdio mode)...")
        
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

def main():
    """Main entry point"""
    # Get configuration from environment
    host = os.environ.get('CFS_HOST', 'localhost')
    port = int(os.environ.get('CFS_PORT', '8765'))
    
    # Create and run server
    server = WindowsCFSMCPServer(host, port)
    
    try:
        asyncio.run(server.run_stdio())
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
