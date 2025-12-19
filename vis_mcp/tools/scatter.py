"""Scatter plot visualization tools."""

from typing import List, Optional

import matplotlib.pyplot as plt
import numpy as np

from config import default_config
from plot_utils import handle_plot_errors, save_and_show_plot


@handle_plot_errors("scatter plot")
async def create_scatter_plot(
    x_data: List[float],
    y_data: List[float],
    labels: Optional[List[str]] = None,
    colors: Optional[List[str]] = None,
    title: str = "Scatter Plot",
    x_label: str = "X-axis",
    y_label: str = "Y-axis",
    size: int = 50
) -> str:
    """Create a scatter plot."""
    plt.figure(figsize=default_config.figsize_large)
    if colors is None:
        colors = ['blue'] * len(x_data)
    
    plt.scatter(
        x_data, y_data, c=colors, s=size, 
        alpha=default_config.scatter_alpha, 
        edgecolors='black', 
        linewidth=default_config.edge_linewidth
    )
    
    if labels:
        for i, label in enumerate(labels):
            if i < len(x_data) and i < len(y_data):
                plt.annotate(
                    label, (x_data[i], y_data[i]), 
                    xytext=(5, 5), textcoords='offset points',
                    fontsize=10, alpha=0.8
                )
    
    plt.xlabel(x_label, fontsize=default_config.label_fontsize)
    plt.ylabel(y_label, fontsize=default_config.label_fontsize)
    plt.title(title, fontsize=default_config.title_fontsize, fontweight='bold')
    plt.grid(True, alpha=default_config.grid_alpha)
    plt.tight_layout()
    
    return save_and_show_plot("scatter_plot")


@handle_plot_errors("classification plot")
async def create_classification_plot(
    x_data: List[float],
    y_data: List[float],
    categories: List[str],
    title: str = "Classification Scatter Plot",
    x_label: str = "Feature 1",
    y_label: str = "Feature 2"
) -> str:
    """Create a scatter plot with classification categories."""
    plt.figure(figsize=default_config.figsize_large)
    unique_categories = list(set(categories))
    colors = plt.cm.Set1(np.linspace(0, 1, len(unique_categories)))
    
    for i, category in enumerate(unique_categories):
        mask = [cat == category for cat in categories]
        x_cat = [x for x, m in zip(x_data, mask) if m]
        y_cat = [y for y, m in zip(y_data, mask) if m]
        plt.scatter(
            x_cat, y_cat, c=[colors[i]], label=category, 
            s=60, alpha=default_config.scatter_alpha, 
            edgecolors='black', 
            linewidth=default_config.edge_linewidth
        )
    
    plt.xlabel(x_label, fontsize=default_config.label_fontsize)
    plt.ylabel(y_label, fontsize=default_config.label_fontsize)
    plt.title(title, fontsize=default_config.title_fontsize, fontweight='bold')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, alpha=default_config.grid_alpha)
    plt.tight_layout()
    
    return save_and_show_plot("classification_plot")
