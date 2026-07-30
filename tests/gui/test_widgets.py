"""Tests for common GUI widgets and actions."""

from PyQt6.QtWidgets import QWidget

from wcl_analyzer.gui.actions import AppActions
from wcl_analyzer.gui.widgets import AppButton


def test_app_button_synchronizes_with_bound_action(qtbot) -> None:
    parent = QWidget()
    qtbot.addWidget(parent)
    actions = AppActions(parent)
    button = AppButton(actions.load_report, object_name="loadButton")
    qtbot.addWidget(button)

    assert button.text() == "불러오기"
    assert button.isEnabled()

    actions.load_report.setText("불러오는 중...")
    actions.load_report.setEnabled(False)

    assert button.text() == "불러오는 중..."
    assert not button.isEnabled()


def test_app_button_triggers_bound_action(qtbot) -> None:
    parent = QWidget()
    qtbot.addWidget(parent)
    actions = AppActions(parent)
    button = AppButton(actions.load_report, object_name="loadButton")
    qtbot.addWidget(button)
    triggered: list[bool] = []
    actions.load_report.triggered.connect(triggered.append)

    button.click()

    assert triggered == [False]
