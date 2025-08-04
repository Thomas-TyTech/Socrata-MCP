# Socrata MCP Server

A Model Context Protocol (MCP) server that enables AI agents to query Socrata open data platforms using natural language and generate insights from the data.

## Status: ✅ Working

The server has been tested and is fully functional. All core features are working correctly:
- ✅ MCP server initialization and communication
- ✅ Dataset querying with SoQL
- ✅ Dataset search functionality  
- ✅ Dataset metadata retrieval
- ✅ Resource access (popular domains, example queries)
- ✅ All 5 tools functioning properly

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
python test_server.py
python test_mcp_functionality.py
```

## Usage

### Running the MCP Server

```bash
# Start the server
python -m socrata_mcp.server
```

### Configuration

The server accepts an optional Socrata application token for higher rate limits. Set the `SOCRATA_APP_TOKEN` environment variable:

```bash
export SOCRATA_APP_TOKEN=your_token_here
```

### Available Tools

1. **query_dataset**: Execute SoQL queries
2. **search_datasets**: Search for datasets by keywords
3. **get_dataset_info**: Get dataset metadata and schema
4. **natural_language_query**: Convert natural language to SoQL
5. **analyze_data**: Generate insights from query results

### Example Usage with Claude Desktop

Add this server to your Claude Desktop MCP configuration:

```json
{
  "mcpServers": {
    "socrata": {
      "command": "python",
      "args": ["-m", "socrata_mcp.server"],
      "cwd": "/path/to/socrata-mcp"
    }
  }
}
```

## SoQL Query Examples

```sql
-- Get all records
SELECT *

-- Filter by conditions
SELECT * WHERE category = 'THEFT' AND year = 2023

-- Aggregate functions
SELECT COUNT(*) as total_crimes, primary_type
WHERE year = 2023
GROUP BY primary_type
ORDER BY total_crimes DESC

-- Date filtering
SELECT * WHERE date_trunc_ymd(date) = '2023-01-01'

-- Geospatial queries
SELECT * WHERE within_circle(location, 41.8781, -87.6298, 1000)
```

## Common Socrata Domains

- `data.cityofchicago.org` - Chicago Open Data
- `data.seattle.gov` - Seattle Open Data
- `data.sfgov.org` - San Francisco Open Data
- `data.ny.gov` - New York State Open Data
- `opendata.dc.gov` - Washington DC Open Data

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
# Basic import and client tests
python test_server.py

# Full MCP functionality tests
python test_mcp_functionality.py
```

### Recent Fixes

- ✅ Fixed duplicate LIMIT clause issue in SoQL queries
- ✅ Improved error handling for search timeouts
- ✅ Added proper query cleaning and validation

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
