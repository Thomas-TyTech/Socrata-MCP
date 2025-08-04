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

This is an **MCP (Model Context Protocol) server** that needs to be used with an MCP-compatible client. It cannot be used standalone - you must configure it with one of the supported clients below.

### Supported MCP Clients

- **[Cline](https://github.com/cline/cline)** - VS Code extension for AI-powered coding
- **[Claude Desktop](https://claude.ai/desktop)** - Anthropic's desktop application
- **[Claude Code](https://marketplace.visualstudio.com/items?itemName=Anthropic.claude-vscode)** - VS Code extension by Anthropic

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
        "SOCRATA_APP_TOKEN": "your_app_token_here_optional"
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

The AI assistant will use the Socrata MCP tools to search for relevant datasets, query the data, and provide insights.


## Troubleshooting

### Common Issues

1. **Query Syntax Errors**: 
   - Don't include `FROM` clauses in SoQL queries - the dataset is implicit from the API endpoint
   - Avoid duplicate `LIMIT` clauses - the server automatically handles limits

2. **Rate Limiting**:
   - Get a free Socrata app token from [dev.socrata.com](https://dev.socrata.com/register)
   - Set the `SOCRATA_APP_TOKEN` environment variable

3. **Dataset Not Found**:
   - Verify the domain and dataset ID are correct
   - Use the search tool to find available datasets

4. **Connection Issues**:
   - Check internet connectivity
   - Some domains may have different API endpoints

### Testing

Run the test suite to verify everything is working:

```bash
# Full MCP functionality tests
python examples/test_functionality.py

# Example usage demonstrations
python examples/example_queries.py
```

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run type checking
mypy socrata_mcp/

# Format code
black socrata_mcp/
```

## License

MIT License
