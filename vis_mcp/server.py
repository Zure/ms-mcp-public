"""Visualization MCP Server - Provides tools for creating various plots and charts."""

from fastmcp import FastMCP

from tools import (
    create_relationship_graph,
    create_scatter_plot,
    create_classification_plot,
    create_histogram,
    create_line_plot,
    create_heatmap,
    create_pie_chart,
)

# Initialize FastMCP server
mcp = FastMCP(name="MSLab/Visualization")

# Register all tools
mcp.tool()(create_relationship_graph)
mcp.tool()(create_scatter_plot)
mcp.tool()(create_classification_plot)
mcp.tool()(create_histogram)
mcp.tool()(create_line_plot)
mcp.tool()(create_heatmap)
mcp.tool()(create_pie_chart)

if __name__ == "__main__":
    mcp.run(transport='stdio')
