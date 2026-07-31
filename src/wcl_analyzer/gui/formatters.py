"""Shared formatting helpers for GUI presentation values."""


def format_elapsed_ms(elapsed_ms: int | None) -> str:
    """Format elapsed milliseconds as ``MM.SS.mmm`` or ``None``."""
    if elapsed_ms is None:
        return "None"
    minutes, remainder_ms = divmod(max(0, elapsed_ms), 60_000)
    seconds, milliseconds = divmod(remainder_ms, 1_000)
    return f"{minutes:02d}.{seconds:02d}.{milliseconds:03d}"
