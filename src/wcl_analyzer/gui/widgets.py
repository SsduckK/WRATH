"""Common WRATH widget classes."""

from collections.abc import Iterable

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QComboBox, QPushButton, QWidget

from wcl_analyzer.domain import Fight


class AppButton(QPushButton):
    """A common WRATH button whose command is provided by a QAction."""

    def __init__(
        self,
        action: QAction,
        *,
        object_name: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._action = action

        self.setObjectName(object_name)
        self.setMinimumHeight(32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.clicked.connect(self._action.trigger)
        self._action.changed.connect(self._sync_from_action)
        self._sync_from_action()

    def _sync_from_action(self) -> None:
        """Synchronize presentation state from the bound QAction."""
        self.setText(self._action.text())
        self.setIcon(self._action.icon())
        self.setToolTip(self._action.toolTip())
        self.setStatusTip(self._action.statusTip())
        self.setEnabled(self._action.isEnabled())


class FightSelector(QComboBox):
    """Display Fight models and emit the selected Fight."""

    fight_selected = pyqtSignal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("fightCombo")
        self.setEnabled(False)
        self.activated.connect(self._emit_selected_fight)

    def set_fights(self, fights: Iterable[Fight]) -> None:
        """Replace the selector contents with domain Fight models."""
        self.blockSignals(True)
        self.clear()
        for fight in fights:
            self.addItem(self._format_fight(fight), userData=fight)
        self.blockSignals(False)

        has_fights = self.count() > 0
        self.setEnabled(has_fights)
        if has_fights:
            self.setCurrentIndex(0)

    def clear_fights(self) -> None:
        """Clear all fights and disable selection."""
        self.clear()
        self.setEnabled(False)

    def _emit_selected_fight(self, index: int) -> None:
        fight = self.itemData(index)
        if isinstance(fight, Fight):
            self.fight_selected.emit(fight)

    @staticmethod
    def _format_fight(fight: Fight) -> str:
        duration_seconds = fight.duration_ms / 1_000
        return f"{fight.id}. {fight.name} ({duration_seconds:.1f}초)"
