"""Socrata MCP Server implementation."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
import os

import mcp.server.stdio
import mcp.types as types
from mcp.server import Server
from mcp.server.models import InitializationOptions, ServerCapabilities
from pydantic import AnyUrl

from .socrata_client import SocrataClient

# Configure logging to stderr with appropriate level for production
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Initialize the MCP server
server = Server("socrata-mcp")

# Initialize Socrata client with optional app token
app_token = os.getenv("SOCRATA_APP_TOKEN")
socrata_client = SocrataClient(app_token=app_token, timeout=60.0)  # Increase timeout


@server.list_resources()
async def handle_list_resources() -> List[types.Resource]:
    """List available Socrata resources."""
    return [
        types.Resource(
            uri="socrata://popular-domains",
            name="Popular Socrata Domains",
            description="List of popular Socrata domains and their information",
            mimeType="application/json",
        ),
        types.Resource(
            uri="socrata://example-queries",
            name="Example SoQL Queries",
            description="Common SoQL query patterns and examples",
            mimeType="application/json",
        ),
    ]


@server.list_resource_templates()
async def handle_list_resource_templates() -> List[types.ResourceTemplate]:
    """List available Socrata resource templates."""
    return [
        types.ResourceTemplate(
            uriTemplate="socrata://dataset/{domain}/{dataset_id}",
            name="dataset-info",
            description="Get detailed information about a specific dataset",
            mimeType="application/json",
        ),
        types.ResourceTemplate(
            uriTemplate="socrata://domain/{domain}/datasets",
            name="domain-datasets",
            description="List all datasets available on a Socrata domain",
            mimeType="application/json",
        ),
        types.ResourceTemplate(
            uriTemplate="socrata://schema/{domain}/{dataset_id}",
            name="dataset-schema",
            description="Get the schema/column information for a dataset",
            mimeType="application/json",
        ),
    ]


@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """Read a Socrata resource."""
    uri_str = str(uri)
    logger.info(f"Reading resource: {uri_str}")
    
    try:
        if uri_str == "socrata://popular-domains":
            domains = {
                "popular_domains": [
                    {
                        "domain": "data.cityofchicago.org",
                        "name": "City of Chicago",
                        "description": "Chicago's official open data portal",
                        "categories": ["crime", "transportation", "permits", "budget"]
                    },
                    {
                        "domain": "data.seattle.gov",
                        "name": "City of Seattle",
                        "description": "Seattle's open data portal",
                        "categories": ["crime", "transportation", "permits", "environment"]
                    },
                    {
                        "domain": "data.sfgov.org",
                        "name": "City of San Francisco",
                        "description": "San Francisco's open data portal",
                        "categories": ["crime", "transportation", "housing", "environment"]
                    },
                    {
                        "domain": "data.montgomerycountymd.gov",
                        "name": "Montgomery County, MD",
                        "description": "Montgomery County Maryland open data",
                        "categories": ["crime", "health", "permits", "budget"]
                    }
                ]
            }
            return json.dumps(domains, indent=2)
            
        elif uri_str == "socrata://example-queries":
            examples = {
                "important_note": "Do not include FROM clauses in SoQL queries. The dataset is implicit from the API endpoint.",
                "example_queries": [
                    {
                        "description": "Get all records with limit",
                        "query": "SELECT * LIMIT 100",
                        "use_case": "Basic data exploration"
                    },
                    {
                        "description": "Filter by date range",
                        "query": "SELECT * WHERE date >= '2024-01-01' AND date <= '2024-12-31'",
                        "use_case": "Time-based filtering"
                    },
                    {
                        "description": "Count records by category", 
                        "query": "SELECT category, COUNT(*) AS count GROUP BY category",
                        "use_case": "Aggregation and grouping"
                    },
                    {
                        "description": "Time series analysis",
                        "query": "SELECT year, COUNT(*) as total WHERE year >= 2020 GROUP BY year ORDER BY year",
                        "use_case": "Yearly aggregation and trends"
                    },
                    {
                        "description": "Search text fields",
                        "query": "SELECT * WHERE description LIKE '%crime%'",
                        "use_case": "Text search"
                    },
                    {
                        "description": "Geographic filtering",
                        "query": "SELECT * WHERE within_circle(location, 41.8781, -87.6298, 1000)",
                        "use_case": "Location-based queries"
                    }
                ]
            }
            return json.dumps(examples, indent=2)
            
        elif uri_str.startswith("socrata://dataset/"):
            # Parse template: socrata://dataset/{domain}/{dataset_id}
            parts = uri_str.replace("socrata://dataset/", "").split("/")
            if len(parts) >= 2:
                domain, dataset_id = parts[0], parts[1]
                result = await socrata_client.get_dataset_info(domain, dataset_id)
                return json.dumps(result, indent=2)
            else:
                return json.dumps({"error": "Invalid dataset URI format"})
                
        elif uri_str.startswith("socrata://domain/") and uri_str.endswith("/datasets"):
            # Parse template: socrata://domain/{domain}/datasets
            domain = uri_str.replace("socrata://domain/", "").replace("/datasets", "")
            result = await socrata_client.search_datasets(domain, "*", limit=50)
            return json.dumps({"datasets": result}, indent=2)
            
        elif uri_str.startswith("socrata://schema/"):
            # Parse template: socrata://schema/{domain}/{dataset_id}
            parts = uri_str.replace("socrata://schema/", "").split("/")
            if len(parts) >= 2:
                domain, dataset_id = parts[0], parts[1]
                dataset_info = await socrata_client.get_dataset_info(domain, dataset_id)
                schema = {
                    "dataset_id": dataset_id,
                    "name": dataset_info.get("name", ""),
                    "columns": dataset_info.get("columns", [])
                }
                return json.dumps(schema, indent=2)
            else:
                return json.dumps({"error": "Invalid schema URI format"})
        else:
            return json.dumps({"error": f"Unknown resource: {uri_str}"})
            
    except Exception as e:
        logger.error(f"Error reading resource {uri_str}: {e}")
        return json.dumps({"error": str(e)})


@server.list_prompts()
async def handle_list_prompts() -> List[types.Prompt]:
    """List available Socrata prompts."""
    return [
        types.Prompt(
            name="explore-dataset",
            description="Explore a Socrata dataset with guided questions",
            arguments=[
                types.PromptArgument(
                    name="domain",
                    description="Socrata domain (e.g. data.cityofchicago.org)",
                    required=True,
                ),
                types.PromptArgument(
                    name="dataset_id",
                    description="Dataset ID (4x4 format like 'abcd-1234')",
                    required=True,
                ),
                types.PromptArgument(
                    name="focus_area",
                    description="What aspect to focus on (trends, patterns, anomalies, summary)",
                    required=False,
                ),
            ],
        ),
        types.Prompt(
            name="find-crime-data",
            description="Find and analyze crime datasets across domains",
            arguments=[
                types.PromptArgument(
                    name="location",
                    description="City or region to search (e.g. Chicago, Seattle)",
                    required=True,
                ),
                types.PromptArgument(
                    name="crime_type",
                    description="Type of crime to focus on (optional)",
                    required=False,
                ),
                types.PromptArgument(
                    name="time_period",
                    description="Time period to analyze (e.g. 2024, last-year)",
                    required=False,
                ),
            ],
        ),
        types.Prompt(
            name="compare-cities",
            description="Compare data between multiple cities",
            arguments=[
                types.PromptArgument(
                    name="cities",
                    description="Comma-separated list of cities to compare",
                    required=True,
                ),
                types.PromptArgument(
                    name="metric",
                    description="What to compare (crime, permits, budget, etc.)",
                    required=True,
                ),
                types.PromptArgument(
                    name="year",
                    description="Year to focus the comparison on",
                    required=False,
                ),
            ],
        ),
    ]


@server.get_prompt()
async def handle_get_prompt(name: str, arguments: Optional[Dict[str, str]]) -> types.GetPromptResult:
    """Get a specific prompt with its content."""
    if arguments is None:
        arguments = {}
        
    try:
        if name == "explore-dataset":
            domain = arguments.get("domain", "")
            dataset_id = arguments.get("dataset_id", "")
            focus_area = arguments.get("focus_area", "summary")
            
            prompt_content = f"""I want to explore the dataset {dataset_id} on {domain}.

Please help me understand this dataset by:

1. First, get the dataset information to understand its structure and contents
2. Show me a sample of the data to see what it looks like
3. Focus on {focus_area} - provide insights about this aspect
4. Suggest some interesting questions I could ask about this data

Dataset: {domain}/{dataset_id}
Focus: {focus_area}

Start by using the get_dataset_info tool to understand the dataset structure."""

            return types.GetPromptResult(
                description=f"Explore dataset {dataset_id} focusing on {focus_area}",
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(type="text", text=prompt_content),
                    )
                ],
            )
            
        elif name == "find-crime-data":
            location = arguments.get("location", "")
            crime_type = arguments.get("crime_type", "")
            time_period = arguments.get("time_period", "")
            
            domain_mapping = {
                "chicago": "data.cityofchicago.org",
                "seattle": "data.seattle.gov", 
                "san francisco": "data.sfgov.org",
                "montgomery county": "data.montgomerycountymd.gov"
            }
            
            domain = domain_mapping.get(location.lower(), "")
            search_terms = f"crime {crime_type}".strip()
            
            prompt_content = f"""I want to find and analyze crime data for {location}.

Please help me by:

1. Search for crime-related datasets {"on " + domain if domain else "across available domains"}
2. Show me the available crime datasets and their details
3. {"Focus on " + crime_type + " crimes specifically" if crime_type else "Show me the types of crimes available"}
4. {"Analyze data for " + time_period if time_period else "Show me the time range of available data"}
5. Provide insights about crime patterns and trends

Location: {location}
{"Crime Type: " + crime_type if crime_type else ""}
{"Time Period: " + time_period if time_period else ""}

Start by searching for datasets with the term "{search_terms}"."""

            return types.GetPromptResult(
                description=f"Find and analyze crime data for {location}",
                messages=[
                    types.PromptMessage(
                        role="user", 
                        content=types.TextContent(type="text", text=prompt_content),
                    )
                ],
            )
            
        elif name == "compare-cities":
            cities = arguments.get("cities", "")
            metric = arguments.get("metric", "")
            year = arguments.get("year", "")
            
            prompt_content = f"""I want to compare {metric} data between these cities: {cities}.

Please help me by:

1. For each city, search for datasets related to {metric}
2. Identify comparable datasets across the cities
3. Show me the data structure and what metrics are available
4. {"Focus on data from " + year if year else "Use the most recent complete year of data"}
5. Create a comparison showing differences and similarities
6. Provide insights about what the differences might mean

Cities to compare: {cities}
Metric: {metric}
{"Year: " + year if year else ""}

Start by searching for {metric} datasets in each city's open data portal."""

            return types.GetPromptResult(
                description=f"Compare {metric} between {cities}",
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(type="text", text=prompt_content),
                    )
                ],
            )
        else:
            raise ValueError(f"Unknown prompt: {name}")
            
    except Exception as e:
        logger.error(f"Error getting prompt {name}: {e}")
        raise


@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available Socrata tools."""
    return [
        types.Tool(
            name="query_dataset",
            description="Execute SoQL (Socrata Query Language) queries on datasets to retrieve specific data",
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Socrata domain hostname",
                        "examples": ["data.cityofchicago.org", "data.seattle.gov", "data.sfgov.org"],
                    },
                    "dataset_id": {
                        "type": "string",
                        "description": "Dataset identifier in 4x4 format (e.g., 'abcd-1234')",
                        "pattern": "^[a-z0-9]{4}-[a-z0-9]{4}$",
                        "examples": ["ijzp-q8t2", "crimes-data-123", "permits-2024"],
                    },
                    "query": {
                        "type": "string",
                        "description": "SoQL query string using Socrata Query Language syntax. Do not include FROM clauses - the dataset is implicit from the endpoint.",
                        "examples": [
                            "SELECT * LIMIT 100",
                            "SELECT date, count(*) GROUP BY date ORDER BY date DESC",
                            "SELECT * WHERE date >= '2024-01-01' AND primary_type = 'THEFT'",
                            "SELECT year, COUNT(*) as total WHERE year >= 2020 GROUP BY year ORDER BY year"
                        ],
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of rows to return",
                        "default": 1000,
                        "minimum": 1,
                        "maximum": 50000,
                    },
                    "format": {
                        "type": "string",
                        "enum": ["json", "csv", "geojson"],
                        "description": "Output format for the results",
                        "default": "json",
                    },
                },
                "required": ["domain", "dataset_id", "query"],
            },
        ),
        types.Tool(
            name="search_datasets",
            description="Search and discover datasets on Socrata domains using keywords",
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Socrata domain to search within",
                        "examples": ["data.cityofchicago.org", "data.seattle.gov", "data.montgomerycountymd.gov"],
                    },
                    "query": {
                        "type": "string",
                        "description": "Search keywords or phrases to find relevant datasets",
                        "examples": ["crime", "police incidents", "building permits", "budget", "transportation"],
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of datasets to return",
                        "default": 20,
                        "minimum": 1,
                        "maximum": 100,
                    },
                },
                "required": ["domain", "query"],
            },
        ),
        types.Tool(
            name="get_dataset_info",
            description="Get comprehensive metadata, schema, and column information for a specific dataset",
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Socrata domain hosting the dataset",
                        "examples": ["data.cityofchicago.org", "data.seattle.gov"],
                    },
                    "dataset_id": {
                        "type": "string",
                        "description": "Unique dataset identifier in 4x4 format",
                        "pattern": "^[a-z0-9]{4}-[a-z0-9]{4}$",
                        "examples": ["ijzp-q8t2", "crimes-data-123"],
                    },
                },
                "required": ["domain", "dataset_id"],
            },
        ),
        types.Tool(
            name="natural_language_query",
            description="Convert natural language questions into executable SoQL queries and optionally run them",
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Socrata domain for the dataset",
                        "examples": ["data.cityofchicago.org", "data.seattle.gov"],
                    },
                    "dataset_id": {
                        "type": "string",
                        "description": "Dataset identifier to query against",
                        "pattern": "^[a-z0-9]{4}-[a-z0-9]{4}$",
                    },
                    "question": {
                        "type": "string",
                        "description": "Natural language question about the data",
                        "examples": [
                            "How many crimes happened last year?",
                            "What are the most common types of incidents?", 
                            "Show me all theft cases in downtown area"
                        ],
                    },
                    "execute": {
                        "type": "boolean",
                        "description": "Whether to execute the generated query and return results",
                        "default": True,
                    },
                },
                "required": ["domain", "dataset_id", "question"],
            },
        ),
        types.Tool(
            name="analyze_data",
            description="Perform statistical analysis and generate insights from query results",
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Socrata domain for the dataset",
                        "examples": ["data.cityofchicago.org", "data.seattle.gov"],
                    },
                    "dataset_id": {
                        "type": "string",
                        "description": "Dataset identifier to analyze",
                        "pattern": "^[a-z0-9]{4}-[a-z0-9]{4}$",
                    },
                    "query": {
                        "type": "string",
                        "description": "SoQL query to analyze results from",
                        "examples": [
                            "SELECT * WHERE date >= '2024-01-01'",
                            "SELECT primary_type, count(*) GROUP BY primary_type"
                        ],
                    },
                    "analysis_type": {
                        "type": "string",
                        "enum": ["summary", "trends", "correlations", "anomalies"],
                        "description": "Type of statistical analysis to perform",
                        "default": "summary",
                    },
                },
                "required": ["domain", "dataset_id", "query"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: Optional[Dict[str, Any]]
) -> List[types.TextContent]:
    """Handle tool execution requests."""
    logger.info(f"Received tool call: {name} with arguments: {arguments}")
    
    if arguments is None:
        arguments = {}

    try:
        if name == "query_dataset":
            result = await socrata_client.query_dataset(
                domain=arguments["domain"],
                dataset_id=arguments["dataset_id"],
                query=arguments["query"],
                limit=arguments.get("limit", 1000),
                format=arguments.get("format", "json"),
            )
            if isinstance(result, str):
                return [types.TextContent(type="text", text=result)]
            else:
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "search_datasets":
            # Validate required arguments
            if "domain" not in arguments:
                return [types.TextContent(type="text", text="Error: 'domain' parameter is required")]
            if "query" not in arguments:
                return [types.TextContent(type="text", text="Error: 'query' parameter is required")]
                
            logger.info(f"Searching datasets on {arguments['domain']} with query: {arguments['query']}")
            
            try:
                # Add timeout protection
                import asyncio
                result = await asyncio.wait_for(
                    socrata_client.search_datasets(
                        domain=arguments["domain"],
                        query=arguments["query"],
                        limit=min(arguments.get("limit", 20), 50),  # Cap at 50 results
                    ),
                    timeout=30.0  # 30 second timeout
                )
                logger.info(f"Search returned {len(result) if isinstance(result, list) else 'unknown'} results")
                
                # Create response with size limit
                response_text = json.dumps(result, indent=2)
                
                # If response is too large, truncate and add summary
                if len(response_text) > 50000:  # 50KB limit
                    truncated_result = result[:5] if isinstance(result, list) else result
                    response_text = json.dumps({
                        "note": f"Response truncated - showing first 5 of {len(result)} results. Use smaller limit for full results.",
                        "results": truncated_result
                    }, indent=2)
                
                logger.info(f"Response size: {len(response_text)} chars")
                return [types.TextContent(type="text", text=response_text)]
                
            except asyncio.TimeoutError:
                logger.error(f"Search timed out after 30 seconds")
                return [types.TextContent(type="text", text="Error: Search request timed out. Try with a more specific query.")]
            except Exception as search_error:
                logger.error(f"Search error: {search_error}")
                # Provide a fallback with basic information
                return [types.TextContent(type="text", text=json.dumps({
                    "error": f"Search failed: {str(search_error)}",
                    "suggestion": "Try a more specific search term or check the domain name",
                    "popular_datasets": [
                        {"id": "ijzp-q8t2", "name": "Crimes - 2001 to Present", "domain": "data.cityofchicago.org"},
                        {"id": "wrvz-psew", "name": "Police Stations", "domain": "data.cityofchicago.org"}
                    ]
                }, indent=2))]

        elif name == "get_dataset_info":
            result = await socrata_client.get_dataset_info(
                domain=arguments["domain"],
                dataset_id=arguments["dataset_id"],
            )
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "natural_language_query":
            result = await socrata_client.natural_language_query(
                domain=arguments["domain"],
                dataset_id=arguments["dataset_id"],
                question=arguments["question"],
                execute=arguments.get("execute", True),
            )
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "analyze_data":
            result = await socrata_client.analyze_data(
                domain=arguments["domain"],
                dataset_id=arguments["dataset_id"],
                query=arguments["query"],
                analysis_type=arguments.get("analysis_type", "summary"),
            )
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        else:
            return [
                types.TextContent(
                    type="text", text=f"Unknown tool: {name}"
                )
            ]

    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return [
            types.TextContent(
                type="text", text=f"Error executing {name}: {str(e)}"
            )
        ]


async def main():
    """Run the Socrata MCP server."""
    try:
        logger.info("Starting Socrata MCP server...")
        logger.info(f"App token configured: {'Yes' if app_token else 'No'}")
        
        # Run the server using stdin/stdout streams
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            logger.info("Server streams established, starting MCP server...")
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="socrata-mcp",
                    server_version="0.1.0",
                    capabilities=ServerCapabilities(),
                ),
            )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise


def cli_main():
    """Console script entry point."""
    asyncio.run(main())


if __name__ == "__main__":
    cli_main()
