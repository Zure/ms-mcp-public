"""Configuration settings for the visualization MCP server."""

from dataclasses import dataclass


@dataclass
class PlotConfig:
    """Common plot styling configuration."""
    figsize_large: tuple = (10, 8)
    figsize_medium: tuple = (10, 6)
    title_fontsize: int = 16
    label_fontsize: int = 12
    grid_alpha: float = 0.3
    scatter_alpha: float = 0.7
    edge_linewidth: float = 0.5


# Default configuration instance
default_config = PlotConfig()
