#!/usr/bin/env python3
"""Simple test script to verify the server can be imported without errors."""

import sys
import asyncio

def test_import():
    """Test that we can import the server modules."""
    try:
        from socrata_mcp.server import server, socrata_client
        from socrata_mcp.socrata_client import SocrataClient
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

async def test_client():
    """Test basic client functionality."""
    try:
        from socrata_mcp.socrata_client import SocrataClient
        client = SocrataClient()
        
        # Test that the client can be created
        print("✅ SocrataClient created successfully")
        
        # Close the client
        await client.client.aclose()
        return True
    except Exception as e:
        print(f"❌ Client test error: {e}")
        return False

async def main():
    """Run all tests."""
    print("Testing Socrata MCP Server...")
    
    # Test imports
    if not test_import():
        sys.exit(1)
    
    # Test client
    if not await test_client():
        sys.exit(1)
    
    print("✅ All tests passed! Server should work correctly.")

if __name__ == "__main__":
    asyncio.run(main())