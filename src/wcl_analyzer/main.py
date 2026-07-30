"""WRATH composition root and application entry point."""

from collections.abc import Sequence

from wcl_analyzer.app import ReportService
from wcl_analyzer.gui.application import create_application
from wcl_analyzer.gui.main_window import MainWindow
from wcl_analyzer.infrastructure.wcl import (
    WclGraphqlClient,
    WclReportRepository,
    WclTokenProvider,
)


def create_main_window() -> MainWindow:
    """Build the main window and its application dependencies."""
    token_provider = WclTokenProvider.from_environment()
    graphql_client = WclGraphqlClient(token_provider)
    repository = WclReportRepository(graphql_client)
    report_service = ReportService(repository)
    return MainWindow(report_service, token_provider)


def main(argv: Sequence[str] | None = None) -> int:
    """Build and run the WRATH desktop application."""
    application = create_application(argv)
    window = create_main_window()
    window.show()
    return application.exec()
