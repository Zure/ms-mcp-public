"""Chart visualization tools."""

from typing import List, Optional

import matplotlib.pyplot as plt

from config import default_config
from plot_utils import handle_plot_errors, save_and_show_plot


@handle_plot_errors("line chart")
async def create_line_plot(
    x_data: List[float],
    y_data: List[float],
    title: str = "Line Chart",
    x_label: str = "X-axis",
    y_label: str = "Y-axis",
    line_style: str = "-",
    color: str = "blue"
) -> str:
    """Create a line chart."""
    plt.figure(figsize=default_config.figsize_medium)
    plt.plot(
        x_data, y_data, 
        linestyle=line_style, color=color, 
        linewidth=2, marker='o', markersize=4
    )
    plt.xlabel(x_label, fontsize=default_config.label_fontsize)
    plt.ylabel(y_label, fontsize=default_config.label_fontsize)
    plt.title(title, fontsize=default_config.title_fontsize, fontweight='bold')
    plt.grid(True, alpha=default_config.grid_alpha)
    plt.tight_layout()
    
    return save_and_show_plot("line_plot")


@handle_plot_errors("heatmap")
async def create_heatmap(
    data: List[List[float]],
    x_labels: Optional[List[str]] = None,
    y_labels: Optional[List[str]] = None,
    title: str = "Heatmap",
    colormap: str = "viridis"
) -> str:
    """Create a heatmap from 2D data."""
    plt.figure(figsize=default_config.figsize_large)
    im = plt.imshow(data, cmap=colormap, aspect='auto')
    
    if x_labels:
        plt.xticks(range(len(x_labels)), x_labels, rotation=45, ha='right')
    if y_labels:
        plt.yticks(range(len(y_labels)), y_labels)
    
    plt.colorbar(im, shrink=0.8)
    plt.title(title, fontsize=default_config.title_fontsize, fontweight='bold')
    plt.tight_layout()
    
    return save_and_show_plot("heatmap")


@handle_plot_errors("pie chart")
async def create_pie_chart(
    values: List[float],
    labels: List[str],
    title: str = "Pie Chart",
    colors: Optional[List[str]] = None,
    explode: Optional[List[float]] = None,
    autopct: str = "%1.1f%%"
) -> str:
    """Create a pie chart.
    
    Args:
        values: List of values for each slice
        labels: List of labels for each slice
        title: Chart title
        colors: Optional list of colors for each slice
        explode: Optional list of explode values (0-1) for each slice
        autopct: Format string for percentage display
    
    Returns:
        Path to the saved chart
    """
    plt.figure(figsize=default_config.figsize_medium)
    plt.pie(
        values,
        labels=labels,
        colors=colors,
        explode=explode,
        autopct=autopct,
        startangle=90,
        textprops={'fontsize': default_config.label_fontsize}
    )
    plt.title(title, fontsize=default_config.title_fontsize, fontweight='bold')
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    plt.tight_layout()
    
    return save_and_show_plot("pie_chart")
