"""PyQt application construction and startup."""

import sys
from collections.abc import Sequence

from PyQt6.QtWidgets import QApplication


def create_application(argv: Sequence[str] | None = None) -> QApplication:
    """Create or return the process-wide Qt application."""
    existing_application = QApplication.instance()
    if existing_application is None:
        arguments = list(argv) if argv is not None else sys.argv
        application = QApplication(arguments)
    else:
        application = existing_application

    application.setApplicationName("WRATH")
    application.setOrganizationName("WRATH")
    return application
