"""GUI tests for background report loading and fight selection."""

from PyQt6.QtCore import Qt, QThread

from wcl_analyzer.app import (
    ApiRateLimitStatus,
    ReportLoadResult,
)
from wcl_analyzer.domain import Fight, Report
from wcl_analyzer.gui.main_window import MainWindow


class FakeReportLoader:
    """Return fixed data while recording the worker thread and input."""

    def __init__(
        self,
        result: ReportLoadResult | None = None,
        error: Exception | None = None,
    ) -> None:
        self.result = result
        self.error = error
        self.inputs: list[str] = []
        self.thread: QThread | None = None

    def load_report(self, report_input: str) -> ReportLoadResult:
        self.inputs.append(report_input)
        self.thread = QThread.currentThread()
        if self.error is not None:
            raise self.error
        assert self.result is not None
        return self.result


def make_report() -> Report:
    """Build fixed report data for GUI tests."""
    return Report(
        code="FakeReport123",
        title="Fixture Raid Night",
        fights=(
            Fight(
                id=1,
                name="First Encounter",
                start_time_ms=1_000,
                end_time_ms=61_000,
            ),
            Fight(
                id=2,
                name="Second Encounter",
                start_time_ms=90_000,
                end_time_ms=210_000,
            ),
        ),
    )


def make_result() -> ReportLoadResult:
    """Build a report result with WCL point usage."""
    return ReportLoadResult(
        report=make_report(),
        rate_limit=ApiRateLimitStatus(
            limit_per_hour=3_600,
            points_spent=117.5,
            points_remaining=3_482.5,
            reset_in_seconds=1_800,
        ),
    )


def test_load_report_populates_fight_combo_from_worker_thread(qtbot, qapp) -> None:
    loader = FakeReportLoader(result=make_result())
    window = MainWindow(loader)
    qtbot.addWidget(window)
    window.show()
    window.report_input.setText(
        "https://www.warcraftlogs.com/reports/FakeReport123"
    )

    qtbot.mouseClick(window.load_button, Qt.MouseButton.LeftButton)

    qtbot.waitUntil(lambda: window.fight_combo.count() == 2)
    qtbot.waitUntil(window.load_button.isEnabled)

    assert loader.inputs == [
        "https://www.warcraftlogs.com/reports/FakeReport123"
    ]
    assert loader.thread is not qapp.thread()
    assert window.fight_combo.isEnabled()
    assert window.fight_combo.itemText(0) == "1. First Encounter (60.0초)"
    assert window.fight_combo.itemData(1) == make_report().fights[1]
    assert "2개 전투" in window.status_label.text()
    assert "3,482.5 / 3,600" in window.rate_limit_label.text()


def test_user_fight_selection_prints_selected_fight(qtbot, capsys) -> None:
    window = MainWindow(FakeReportLoader(result=make_result()))
    qtbot.addWidget(window)
    window.report_input.setText("FakeReport123")
    qtbot.mouseClick(window.load_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.fight_combo.count() == 2)

    window.fight_combo.setCurrentIndex(1)
    window.fight_combo.activated.emit(1)

    output = capsys.readouterr().out
    assert "id=2" in output
    assert "name=Second Encounter" in output
    assert "duration=120000 ms" in output


def test_load_error_is_presented_and_controls_are_restored(qtbot) -> None:
    loader = FakeReportLoader(error=RuntimeError("network unavailable"))
    window = MainWindow(loader)
    qtbot.addWidget(window)
    window.report_input.setText("FakeReport123")

    qtbot.mouseClick(window.load_button, Qt.MouseButton.LeftButton)

    qtbot.waitUntil(lambda: window.load_button.isEnabled())

    assert not window.fight_combo.isEnabled()
    assert "network unavailable" in window.status_label.text()
    assert window.report_input.isEnabled()
