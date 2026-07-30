"""Common WRATH widget classes."""

from collections.abc import Iterable

from PyQt6.QtCore import QModelIndex, Qt, pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHeaderView,
    QPushButton,
    QTableView,
    QWidget,
)

from wcl_analyzer.domain import Actor, Fight
from wcl_analyzer.gui.models import ParticipantTableModel


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


class ParticipantTableView(QTableView):
    """Display fight participants and emit a clicked Actor."""

    player_clicked = pyqtSignal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("participantTable")
        self._participant_model = ParticipantTableModel()
        self.setModel(self._participant_model)
        self.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.clicked.connect(self._emit_clicked_player)

    def set_participants(self, participants: Iterable[Actor]) -> None:
        """Replace the displayed player list."""
        self._participant_model.set_participants(participants)

    def clear_participants(self) -> None:
        """Remove every displayed player."""
        self._participant_model.set_participants(())

    def _emit_clicked_player(self, index: QModelIndex) -> None:
        actor = self._participant_model.actor_at(index.row())
        if actor is not None:
            self.player_clicked.emit(actor)
