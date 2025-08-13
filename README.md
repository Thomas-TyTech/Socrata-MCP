# Socrata MCP Server

A Model Context Protocol (MCP) server that enables AI agents to query Socrata open data platforms using natural language and generate insights from the data.

## Features

- **Query Datasets**: Execute SoQL queries on Socrata datasets with support for JSON, CSV, and GeoJSON formats
- **Search Datasets**: Find datasets by keywords across Socrata domains
- **Dataset Information**: Get metadata and schema information for datasets
- **Natural Language Queries**: Convert natural language questions to SoQL queries (basic implementation)
- **Data Analysis**: Generate insights including summaries, trends, correlations, and anomaly detection

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd socrata-mcp

# Install dependencies
pip install -e .

# Test the installation
python examples/test_functionality.py
```

## Usage with MCP Clients

This is an **MCP (Model Context Protocol) server** that needs to be used with an MCP-compatible client. It cannot be used standalone - you must configure it with a client that supports MCP. There are many and I have listed a few below.

### Supported MCP Clients

- **[Cline](https://github.com/cline/cline)** - VS Code extension for AI-assisted coding with Claude
- **[Claude Desktop](https://claude.ai/download)** - Anthropic's Claude desktop application
- **[Claude Code](https://www.npmjs.com/package/@anthropic-ai/claude-code)** - TUI based npm package by Anthropic

### Configuration for Different Clients

#### Cline (VS Code Extension)

1. Install the Cline extension in VS Code
2. Open Cline settings and add this MCP server configuration:

```json
{
  "mcpServers": {
    "socrata": {
      "command": "python3",
      "args": ["-m", "socrata_mcp.server"],
      "cwd": "/path/to/your/socrata-mcp",
      "env": {
        "SOCRATA_APP_TOKEN": "your_app_token_here_optional"
      }
    }
  }
}
```

#### Claude Desktop

1. Download and install Claude Desktop
2. Open Claude Desktop settings (usually `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS)
3. Add this configuration:

```json
{
  "mcpServers": {
    "socrata": {
      "command": "python3",
      "args": ["-m", "socrata_mcp.server"],
      "cwd": "/path/to/your/socrata-mcp",
      "env": {
        "SOCRATA_APP_TOKEN": "your_app_token_here"
      }
    }
  }
}
```

#### Claude Code (VS Code Extension)

1. Install the Claude Code extension in VS Code
2. Configure the MCP server in your Claude Code settings
3. Use the same configuration format as above

### Configuration Notes

- **Replace `/path/to/your/socrata-mcp`** with the actual path to where you cloned this repository
- **SOCRATA_APP_TOKEN** is optional but recommended for higher rate limits (get one free at [dev.socrata.com](https://dev.socrata.com/register))
- Use `python3` or `python` depending on your system setup
- Make sure you've installed the package first: `pip install -e .`

### Available Tools

Once configured with an MCP client, you'll have access to these tools:

1. **query_dataset**: Execute SoQL queries on Socrata datasets
2. **search_datasets**: Search for datasets by keywords across domains
3. **get_dataset_info**: Get detailed metadata and schema information
4. **natural_language_query**: Convert natural language questions to SoQL queries
5. **analyze_data**: Generate statistical insights from query results

### Example Usage

After configuring with an MCP client, you can ask questions like:

- "Find crime datasets in Chicago"
- "What are the most common types of crimes in Seattle?"
- "Show me building permits issued in San Francisco last year"
- "Analyze traffic accident trends in New York"

The AI assistant you connect the MCP server to will use the Socrata MCP to search for relevant datasets, query the data, and provide insights.



