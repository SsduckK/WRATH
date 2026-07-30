"""Smoke tests for the initial PyQt application shell."""

from PyQt6.QtWidgets import QLabel

from wcl_analyzer.app import ReportLoadResult, TokenStatus
from wcl_analyzer.domain import Report
from wcl_analyzer.gui.application import create_application
from wcl_analyzer.gui.main_window import MainWindow


class EmptyReportLoader:
    """Return an empty report for the initial-window smoke test."""

    def load_report(self, report_input: str) -> ReportLoadResult:
        return ReportLoadResult(
            report=Report(code=report_input, title="Empty Report")
        )


class EmptyTokenStatusProvider:
    """Expose the pre-authentication status for the smoke test."""

    def get_status(self) -> TokenStatus:
        return TokenStatus(
            available=False,
            expires_at=None,
            remaining_seconds=None,
        )


def test_create_application_sets_application_metadata(qapp) -> None:
    application = create_application([])

    assert application is qapp
    assert application.applicationName() == "WRATH"
    assert application.organizationName() == "WRATH"


def test_main_window_has_initial_state(qtbot) -> None:
    window = MainWindow(EmptyReportLoader(), EmptyTokenStatusProvider())
    qtbot.addWidget(window)

    assert window.windowTitle() == "WRATH"
    assert window.findChild(QLabel, "titleLabel").text() == "WRATH"
    assert "입력" in window.findChild(QLabel, "statusLabel").text()
    assert "발급 전" in window.token_status_label.text()
    assert "조회 전" in window.rate_limit_label.text()
    assert not window.fight_combo.isEnabled()
