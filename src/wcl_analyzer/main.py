"""WRATH composition root and application entry point."""

from collections.abc import Sequence

from wcl_analyzer.gui.application import create_application
from wcl_analyzer.gui.main_window import MainWindow


def create_main_window() -> MainWindow:
    """Build the main window and its application dependencies."""
    return MainWindow()


def main(argv: Sequence[str] | None = None) -> int:
    """Build and run the WRATH desktop application."""
    application = create_application(argv)
    window = create_main_window()
    window.show()
    return application.exec()
