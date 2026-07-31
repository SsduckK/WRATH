"""Smoke tests for the initial PyQt application shell."""

from PyQt6.QtWidgets import QFrame, QGroupBox, QLabel, QSplitter

from wcl_analyzer.app import ReportLoadResult
from wcl_analyzer.domain import Report
from wcl_analyzer.gui.application import create_application
from wcl_analyzer.gui.formatters import format_elapsed_ms
from wcl_analyzer.gui.main_window import MainWindow


class EmptyReportLoader:
    """Return an empty report for the initial-window smoke test."""

    def load_report(self, report_input: str) -> ReportLoadResult:
        return ReportLoadResult(report=Report(code=report_input, title="Empty Report"))


def test_create_application_sets_application_metadata(qapp) -> None:
    application = create_application([])

    assert application is qapp
    assert application.applicationName() == "WRATH"
    assert application.organizationName() == "WRATH"


def test_main_window_has_initial_state(qtbot) -> None:
    window = MainWindow(EmptyReportLoader())
    qtbot.addWidget(window)

    assert window.windowTitle() == "WRATH"
    assert window.findChild(QLabel, "titleLabel") is None
    assert "입력" in window.findChild(QLabel, "statusLabel").text()
    assert "조회 전" in window.rate_limit_label.text()
    assert window.player_detail_label.text() == "플레이어를 선택하세요."
    assert not window.fight_combo.isEnabled()
    assert window.findChild(QGroupBox, "reportLoadArea") is not None
    assert window.findChild(QFrame, "interactionOutputArea") is not None
    assert window.findChild(QFrame, "playerFilterArea") is not None
    assert window.findChild(QSplitter, "contentSplitter").count() == 2
    assert window.content_splitter.widget(0) is window.interaction_output_area
    assert window.content_splitter.widget(1) is window.player_filter_area
    assert format_elapsed_ms(135_347) == "02.15.347"
    assert format_elapsed_ms(None) == "None"

    window.show()
    qtbot.waitUntil(lambda: sum(window.content_splitter.sizes()) > 0)
    output_width, player_width = window.content_splitter.sizes()
    assert output_width > player_width
