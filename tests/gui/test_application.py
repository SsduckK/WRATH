"""Smoke tests for the initial PyQt application shell."""

from PyQt6.QtWidgets import QLabel

from wcl_analyzer.domain import Report
from wcl_analyzer.gui.application import create_application
from wcl_analyzer.gui.main_window import MainWindow


class EmptyReportLoader:
    """Return an empty report for the initial-window smoke test."""

    def load_report(self, report_input: str) -> Report:
        return Report(code=report_input, title="Empty Report")


def test_create_application_sets_application_metadata(qapp) -> None:
    application = create_application([])

    assert application is qapp
    assert application.applicationName() == "WRATH"
    assert application.organizationName() == "WRATH"


def test_main_window_has_initial_state(qtbot) -> None:
    window = MainWindow(EmptyReportLoader())
    qtbot.addWidget(window)

    assert window.windowTitle() == "WRATH"
    assert window.findChild(QLabel, "titleLabel").text() == "WRATH"
    assert "입력" in window.findChild(QLabel, "statusLabel").text()
    assert not window.fight_combo.isEnabled()
