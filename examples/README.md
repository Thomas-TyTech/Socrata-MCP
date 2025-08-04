# Examples

This directory contains example files and configurations for the Socrata MCP Server.

## Files

### `claude_desktop_config.json`
Example configuration for Claude Desktop MCP settings. Copy this configuration to your Claude Desktop settings and update the `cwd` path to point to your installation directory.

### `example_queries.py`
Demonstrates how to use the Socrata client directly in Python code. Shows examples of:
- Searching for datasets
- Getting dataset information
- Querying datasets with SoQL
- Using natural language queries
- Performing data analysis

### `test_functionality.py`
Comprehensive test script that verifies all MCP server functionality is working correctly. Run this after installation to ensure everything is set up properly.

## Usage

```bash
# Test the MCP server functionality
python examples/test_functionality.py

# Run example queries (requires the server to be installed)
python examples/example_queries.py
```

## Configuration

Before using the examples, make sure you have:

1. Installed the package: `pip install -e .`
2. Optionally set up a Socrata app token: `export SOCRATA_APP_TOKEN=your_token`
3. Updated the `cwd` path in `claude_desktop_config.json` if using with Claude Desktop
