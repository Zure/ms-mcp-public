"""Utility functions for plot creation and management."""

import os
import subprocess
import sys
import tempfile
from datetime import datetime
from functools import wraps
from typing import Callable

import matplotlib
import matplotlib.pyplot as plt

# Use non-interactive backend for server
matplotlib.use('Agg')


def save_and_show_plot(title: str = "plot") -> str:
    """Save the plot to a temporary directory and open it."""
    # Save to temp directory
    temp_dir = tempfile.gettempdir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{title.replace(' ', '_')}_{timestamp}.png"
    filepath = os.path.join(temp_dir, filename)
    
    plt.savefig(filepath, format='png', dpi=150, bbox_inches='tight')
    plt.close()  # Clean up to prevent memory leaks
    
    # Open the image file with the default viewer
    platform = sys.platform
    if platform == 'win32':
        os.startfile(filepath)
    elif platform == 'darwin':  # macOS
        subprocess.run(['open', filepath])
    else:  # Linux
        subprocess.run(['xdg-open', filepath])
    
    return f"Plot saved and opened: {filepath}"


def handle_plot_errors(plot_name: str) -> Callable:
    """Decorator for consistent error handling in plot creation tools."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                return f"Error creating {plot_name}: {str(e)}"
        return wrapper
    return decorator
