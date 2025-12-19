from fastmcp import FastMCP, Context
import logging
from fastmcp.server.auth.providers.azure import AzureProvider
from fastmcp.server.dependencies import get_access_token

auth_provider = AzureProvider(
    tenant_id="",
    client_id="",
    base_url="http://localhost:8010",
    # identifier_uri defaults to api://{client_id}, which matches your Azure config
    required_scopes=["access_as_user"],  # Unprefixed scope name
    client_secret=""
)

mcp = FastMCP(
	name="MSLab/Auth",
	version="0.1.0",
	instructions="Authentication for user in Entra Id",
	auth=auth_provider
)

@mcp.tool
async def get_user_info(ctx: Context) -> dict:
    logging.info("Fetching user info from access token", ctx=ctx)
    
    token = get_access_token()
    # The AzureProvider stores user data in token claims
    return {
        "azure_id": token.claims.get("sub"),
        "email": token.claims.get("email"),
        "name": token.claims.get("name")
    }

if __name__ == "__main__":
	# Run the MCP server over stdio when executed directly.
	mcp.run(transport="http", port=8010, host="127.0.0.1")
