"""
Formatting utilities for Agent Council system.

Provides utilities for formatting outputs, timestamps, and data structures.
"""

import json
from datetime import datetime
from typing import Any

from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table


def format_json(data: Any, indent: int = 2) -> str:
    """
    Format data as pretty-printed JSON.

    Args:
        data: Data to format
        indent: Indentation level

    Returns:
        Formatted JSON string
    """
    return json.dumps(data, indent=indent, default=str, ensure_ascii=False)


def format_timestamp(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime as string.

    Args:
        dt: Datetime to format
        format_str: Format string (strftime compatible)

    Returns:
        Formatted timestamp string
    """
    return dt.strftime(format_str)


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds as human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration (e.g., "2m 30s", "1h 15m")
    """
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def print_json(data: Any, title: str = "JSON Output") -> None:
    """
    Print formatted JSON to console with syntax highlighting.

    Args:
        data: Data to print
        title: Title for the output
    """
    console = Console()
    json_str = format_json(data)
    syntax = Syntax(json_str, "json", theme="monokai", line_numbers=True)
    console.print(f"\n[bold cyan]{title}[/bold cyan]")
    console.print(syntax)


def create_table(
    title: str,
    columns: list[str],
    rows: list[list[Any]],
) -> Table:
    """
    Create a Rich table for console output.

    Args:
        title: Table title
        columns: Column headers
        rows: Table rows

    Returns:
        Rich Table object
    """
    table = Table(title=title, show_header=True, header_style="bold magenta")

    for column in columns:
        table.add_column(column)

    for row in rows:
        table.add_row(*[str(cell) for cell in row])

    return table


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to append when truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def sanitize_for_display(text: str) -> str:
    """
    Sanitize text for display (remove control characters).

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text
    """
    # Remove control characters except newlines and tabs
    return "".join(char for char in text if char.isprintable() or char in "\n\t")

