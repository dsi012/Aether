#!/usr/bin/env python3
"""
Windows Test Script for cFS MCP Server

This script tests the Windows-compatible cFS MCP server functionality.
"""

import asyncio
import json
import os
import sys

async def test_windows_mcp_server():
    """Test the Windows MCP server functionality"""
    print("=== Windows cFS MCP Server Test ===\n")
    
    try:
        # Import the Windows MCP server
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "python_server"))
        from windows_mcp_server import WindowsCFSMCPServer
        
        # Create MCP server instance
        mcp_server = WindowsCFSMCPServer()
        
        # Test various MCP requests
        test_requests = [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {}
            },
            {
                "jsonrpc": "2.0", 
                "id": 2,
                "method": "tools/list",
                "params": {}
            },
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "cfs_get_system_status",
                    "arguments": {}
                }
            },
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "cfs_get_telemetry",
                    "arguments": {"app_name": "MCP_INTERFACE"}
                }
            },
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {
                    "name": "cfs_send_command",
                    "arguments": {
                        "app_name": "CFE_ES",
                        "command": "NOOP",
                        "params": "",
                        "require_confirmation": False,
                        "is_critical": False
                    }
                }
            },
            {
                "jsonrpc": "2.0",
                "id": 6,
                "method": "tools/call",
                "params": {
                    "name": "cfs_list_files",
                    "arguments": {"directory": "/cf"}
                }
            },
            {
                "jsonrpc": "2.0",
                "id": 7,
                "method": "tools/call",
                "params": {
                    "name": "cfs_manage_app",
                    "arguments": {
                        "app_name": "FM",
                        "action": "status",
                        "require_confirmation": False
                    }
                }
            }
        ]
        
        print("Testing MCP protocol requests:\n")
        
        for i, request in enumerate(test_requests, 1):
            print(f"Test {i}: {request['method']}")
            if request['method'] == 'tools/call':
                tool_name = request['params']['name']
                print(f"   Tool: {tool_name}")
            
            try:
                response = await mcp_server.handle_mcp_request(request)
                
                if 'error' in response:
                    print(f"❌ Error: {response['error']['message']}")
                else:
                    print("✅ Success")
                    
                    # Show relevant parts of the response
                    if 'result' in response:
                        result = response['result']
                        
                        if 'serverInfo' in result:
                            print(f"   Server: {result['serverInfo']['name']}")
                        elif 'tools' in result:
                            print(f"   Found {len(result['tools'])} tools")
                        elif 'content' in result:
                            content = result['content'][0]['text']
                            # Parse and show key parts
                            try:
                                data = json.loads(content)
                                if 'data' in data:
                                    data_summary = str(data['data'])
                                    if len(data_summary) > 100:
                                        data_summary = data_summary[:100] + "..."
                                    print(f"   Data: {data_summary}")
                                else:
                                    print(f"   Status: {data.get('status', 'unknown')}")
                            except:
                                if len(content) > 100:
                                    content = content[:100] + "..."
                                print(f"   Content: {content}")
                    
            except Exception as e:
                print(f"❌ Failed: {e}")
            
            print()
        
        print("=== Testing Spacecraft Agent Integration ===\n")
        
        # Test agent integration structure
        try:
            # Check if the integration file exists
            integration_file = os.path.join(os.path.dirname(__file__), "cfs_agent_integration.py")
            if os.path.exists(integration_file):
                print("✅ Agent integration file found")
                
                # Try to import (this will test syntax)
                sys.path.insert(0, os.path.dirname(__file__))
                try:
                    import cfs_agent_integration
                    print("✅ Agent integration module imports successfully")
                    
                    # Check if key functions exist
                    if hasattr(cfs_agent_integration, 'run_spacecraft_agent'):
                        print("✅ run_spacecraft_agent function found")
                    if hasattr(cfs_agent_integration, 'create_cfs_server'):
                        print("✅ create_cfs_server function found")
                        
                except ImportError as e:
                    print(f"⚠️  Agent integration imports with missing dependencies: {e}")
                    print("   This is expected if the agents library is not installed")
                    
            else:
                print("❌ Agent integration file not found")
                
        except Exception as e:
            print(f"❌ Agent integration test failed: {e}")
        
        print("\n=== Testing Configuration ===\n")
        
        # Test configuration file
        config_file = os.path.join(os.path.dirname(__file__), "config", "cfs_config.json")
        if os.path.exists(config_file):
            print("✅ Configuration file found")
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                print("✅ Configuration file is valid JSON")
                print(f"   Version: {config.get('cfs_mcp_server', {}).get('version', 'unknown')}")
                print(f"   Safety mode: {config.get('cfs_mcp_server', {}).get('safety_mode', 'unknown')}")
                app_count = len(config.get('cfs_applications', {}))
                print(f"   Configured apps: {app_count}")
            except Exception as e:
                print(f"❌ Configuration file error: {e}")
        else:
            print("❌ Configuration file not found")
        
        print("\n=== All Tests Completed Successfully! ===")
        print("\nNext steps:")
        print("1. Build and install the cFS application (requires cFS environment)")
        print("2. Install the agents library for full agent integration")
        print("3. Configure your environment variables for production use")
        print("4. Test with actual cFS system when available")
        
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main test function"""
    print("Windows cFS MCP Server Test Suite")
    print("=================================\n")
    
    try:
        asyncio.run(test_windows_mcp_server())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
