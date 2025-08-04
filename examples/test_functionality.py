#!/usr/bin/env python3
"""Comprehensive test of MCP server functionality."""

import asyncio
import json
import sys
from typing import Any, Dict

from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client


async def test_mcp_server():
    """Test the MCP server functionality."""
    print("🧪 Testing Socrata MCP Server functionality...")
    
    try:
        # Start the server process
        from mcp.client.stdio import StdioServerParameters
        
        server_params = StdioServerParameters(
            command="python",
            args=["-m", "socrata_mcp.server"],
            env={}
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                await session.initialize()
                print("✅ MCP session initialized successfully")
                
                # Test 1: List available tools
                tools = await session.list_tools()
                print(f"✅ Found {len(tools.tools)} tools:")
                for tool in tools.tools:
                    print(f"   - {tool.name}: {tool.description}")
                
                # Test 2: List available resources
                resources = await session.list_resources()
                print(f"✅ Found {len(resources.resources)} resources:")
                for resource in resources.resources:
                    print(f"   - {resource.name}: {resource.description}")
                
                # Test 3: Test a simple tool call - get dataset info
                print("\n🔍 Testing get_dataset_info tool...")
                result = await session.call_tool(
                    "get_dataset_info",
                    {
                        "domain": "data.cityofchicago.org",
                        "dataset_id": "ijzp-q8t2"
                    }
                )
                
                if result.content:
                    data = json.loads(result.content[0].text)
                    print(f"✅ Dataset info retrieved: {data.get('name', 'Unknown')}")
                    print(f"   Columns: {len(data.get('columns', []))}")
                    print(f"   Rows: {data.get('rows', 0)}")
                
                # Test 4: Test a query
                print("\n🔍 Testing query_dataset tool...")
                result = await session.call_tool(
                    "query_dataset",
                    {
                        "domain": "data.cityofchicago.org",
                        "dataset_id": "ijzp-q8t2",
                        "query": "SELECT * LIMIT 3",
                        "limit": 3
                    }
                )
                
                if result.content:
                    data = json.loads(result.content[0].text)
                    print(f"✅ Query executed successfully")
                    print(f"   Returned {data.get('total_rows', 0)} rows")
                    print(f"   Execution time: {data.get('execution_time_ms', 0):.2f}ms")
                
                # Test 5: Test search functionality
                print("\n🔍 Testing search_datasets tool...")
                result = await session.call_tool(
                    "search_datasets",
                    {
                        "domain": "data.cityofchicago.org",
                        "query": "crime",
                        "limit": 2
                    }
                )
                
                if result.content:
                    data = json.loads(result.content[0].text)
                    print(f"✅ Search executed successfully")
                    print(f"   Found {len(data)} datasets")
                    for dataset in data[:2]:
                        print(f"   - {dataset.get('name', 'Unknown')} ({dataset.get('id', 'Unknown')})")
                
                # Test 6: Test resource reading
                print("\n🔍 Testing resource reading...")
                resource_result = await session.read_resource("socrata://popular-domains")
                if resource_result.contents:
                    data = json.loads(resource_result.contents[0].text)
                    domains = data.get('popular_domains', [])
                    print(f"✅ Resource read successfully")
                    print(f"   Found {len(domains)} popular domains")
                
                print("\n🎉 All tests passed! The MCP server is working correctly.")
                return True
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run the tests."""
    success = await test_mcp_server()
    if not success:
        sys.exit(1)
    print("\n✅ Socrata MCP Server is ready for use!")


if __name__ == "__main__":
    asyncio.run(main())
