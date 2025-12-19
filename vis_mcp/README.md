# Visualization MCP Server

A Model Context Protocol (MCP) server built with [FastMCP](https://github.com/jlowin/fastmcp) that provides data visualization tools using matplotlib and networkx. When invoked, plots are automatically saved to the system's temp directory and opened in the default image viewer.

## Features

This server exposes 6 visualization tools:

| Tool | Description |
|------|-------------|
| `create_relationship_graph` | Create directed relationship graphs with customizable nodes and edges |
| `create_scatter_plot` | Generate scatter plots with optional labels and colors |
| `create_classification_plot` | Create scatter plots with automatic category coloring |
| `create_histogram` | Generate histograms with configurable bins |
| `create_line_plot` | Create line charts with customizable styling |
| `create_heatmap` | Generate 2D heatmaps from matrix data |

## Project Structure

```
src/
├── server.py          # FastMCP server entry point
├── config.py          # Plot styling configuration
├── plot_utils.py      # Utility functions for saving/displaying plots
└── tools/
    ├── charts.py      # Line plot and heatmap tools
    ├── distributions.py # Histogram tool
    ├── graphs.py      # Relationship graph tool
    └── scatter.py     # Scatter and classification plot tools
```

## Requirements

- Python 3.10+
- Dependencies:
  - `fastmcp` - MCP server framework
  - `matplotlib` - Plotting library
  - `networkx` - Graph visualization
  - `numpy` - Numerical operations

## Installation

1. Clone the repository
2. Create a virtual environment and activate it:
   
   ```bash
   python -m venv venv
   venv\Scripts\activate
   # or on Linux/macOS: source venv/bin/activate
   ```
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the Server

```bash
python -m src.server
```

The server runs using stdio transport for MCP communication.

### VS Code MCP Configuration

Add the following to your MCP client configuration (`.vscode/mcp.json`):

```json
{
  "servers": {
    "visualization": {
      "command": "${workspaceFolder}/venv/Scripts/python.exe",
      "args": ["-m", "src.server"],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

> **Note:** On Linux/macOS, use `${workspaceFolder}/venv/bin/python` instead.

## Tool Examples

### Create Relationship Graph

```json
{
  "nodes": ["A", "B", "C", "D"],
  "edges": [["A", "B"], ["B", "C"], ["C", "D"], ["D", "A"]],
  "title": "My Graph",
  "node_size": 1000,
  "font_size": 12
}
```

### Create Scatter Plot

```json
{
  "x_data": [1, 2, 3, 4, 5],
  "y_data": [2, 4, 6, 8, 10],
  "labels": ["P1", "P2", "P3", "P4", "P5"],
  "title": "Sample Scatter",
  "x_label": "X Values",
  "y_label": "Y Values"
}
```

### Create Classification Plot

```json
{
  "x_data": [1, 2, 3, 4, 5, 6],
  "y_data": [1, 2, 1.5, 4, 5, 4.5],
  "categories": ["A", "A", "A", "B", "B", "B"],
  "title": "Classification Example"
}
```

### Create Histogram

```json
{
  "data": [1, 2, 2, 3, 3, 3, 4, 4, 5],
  "bins": 10,
  "title": "Distribution"
}
```

### Create Line Plot

```json
{
  "x_data": [0, 1, 2, 3, 4],
  "y_data": [0, 1, 4, 9, 16],
  "title": "Quadratic Function",
  "color": "red",
  "line_style": "--"
}
```

### Create Heatmap

```json
{
  "data": [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
  "x_labels": ["A", "B", "C"],
  "y_labels": ["X", "Y", "Z"],
  "colormap": "viridis"
}
```

## Output

All tools are asynchronous and return a success message with the file path. Plots are:
- Saved as PNG files (150 DPI) in the system's temporary directory
- Named with a timestamp (e.g., `scatter_plot_20251212_143022.png`)
- Automatically opened in the default image viewer

## License

MIT
