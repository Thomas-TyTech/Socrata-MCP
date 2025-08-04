# Socrata App Token Setup (Optional)

While the MCP server works without an app token, getting one provides several benefits:

## Benefits of Using an App Token

- **Higher rate limits**: 10,000 requests/hour vs 1,000 requests/hour
- **Better performance**: Faster response times
- **More reliable access**: Reduced chance of rate limiting during heavy usage

## How to Get a Socrata App Token

1. **Visit the Socrata Developer Portal**: Go to https://dev.socrata.com/
2. **Sign up for a free account** if you don't have one
3. **Navigate to "App Tokens"** in your account dashboard
4. **Create a new app token**:
   - Give it a descriptive name (e.g., "MCP Socrata Client")
   - Provide a brief description of your use case
5. **Copy your app token** - it will look like a random string of characters

## Adding the Token to Your Configuration

1. Open your Claude Desktop configuration file
2. Find the `SOCRATA_APP_TOKEN` environment variable
3. Replace the empty string with your actual token:

```json
{
  "mcpServers": {
    "socrata": {
      "command": "python3",
      "args": ["-m", "socrata_mcp.server"],
      "cwd": "/Users/thomasfaulds/Documents/GitHub/socrata-mcp",
      "env": {
        "SOCRATA_APP_TOKEN": "your_actual_token_here"
      }
    }
  }
}
```

4. **Restart Claude Desktop** to apply the changes

## Important Notes

- **Keep your token private**: Don't share it publicly or commit it to version control
- **The server works without a token**: You can leave it empty for basic usage
- **Different domains may have different limits**: Each Socrata domain may have its own rate limiting policies

## Verifying Your Token

Once configured, the MCP server will log whether an app token is configured when it starts up. Look for a message like:
```
App token configured: Yes
```

This confirms your token is being used for API requests.