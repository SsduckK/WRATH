"""Tests for common GUI widgets and actions."""

from PyQt6.QtWidgets import QWidget

from wcl_analyzer.domain import Fight
from wcl_analyzer.gui.actions import AppActions
from wcl_analyzer.gui.widgets import AppButton, FightSelector


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


def test_fight_selector_stores_models_and_emits_selection(qtbot) -> None:
    selector = FightSelector()
    qtbot.addWidget(selector)
    fight = Fight(
        id=3,
        name="Test Encounter",
        start_time_ms=1_000,
        end_time_ms=61_000,
    )
    selected: list[object] = []
    selector.fight_selected.connect(selected.append)

    selector.set_fights((fight,))
    selector.activated.emit(0)

    assert selector.isEnabled()
    assert selector.itemText(0) == "3. Test Encounter (60.0초)"
    assert selector.itemData(0) is fight
    assert selected == [fight]
