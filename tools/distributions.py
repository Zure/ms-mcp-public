"""Distribution visualization tools."""

from typing import List

import matplotlib.pyplot as plt

from config import default_config
from plot_utils import handle_plot_errors, save_and_show_plot


@handle_plot_errors("histogram")
async def create_histogram(
    data: List[float],
    bins: int = 30,
    title: str = "Histogram",
    x_label: str = "Value",
    y_label: str = "Frequency"
) -> str:
    """Create a histogram."""
    plt.figure(figsize=default_config.figsize_medium)
    plt.hist(
        data, bins=bins, 
        alpha=default_config.scatter_alpha, 
        color='skyblue', 
        edgecolor='black', 
        linewidth=default_config.edge_linewidth
    )
    plt.xlabel(x_label, fontsize=default_config.label_fontsize)
    plt.ylabel(y_label, fontsize=default_config.label_fontsize)
    plt.title(title, fontsize=default_config.title_fontsize, fontweight='bold')
    plt.grid(True, alpha=default_config.grid_alpha, axis='y')
    plt.tight_layout()
    
    return save_and_show_plot("histogram")
