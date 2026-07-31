"""Qt item models used by WRATH views."""

from collections.abc import Iterable

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt, QVariant
from PyQt6.QtGui import QColor

from wcl_analyzer.domain import Actor
from wcl_analyzer.gui.gui_config import get_class_style


class ParticipantTableModel(QAbstractTableModel):
    """Expose fight participants as a vertical table."""

    _HEADERS = ("플레이어",)

    def __init__(self) -> None:
        super().__init__()
        self._participants: tuple[Actor, ...] = ()

    def rowCount(self, parent: QModelIndex | None = None) -> int:
        """Return the number of participant rows."""
        return 0 if parent is not None and parent.isValid() else len(self._participants)

    def columnCount(self, parent: QModelIndex | None = None) -> int:
        """Return the number of participant columns."""
        return 0 if parent is not None and parent.isValid() else len(self._HEADERS)

    def data(
        self,
        index: QModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> object:
        """Return display data or the Actor stored at an index."""
        if not index.isValid() or not 0 <= index.row() < len(self._participants):
            return QVariant()

        actor = self._participants[index.row()]
        if role == Qt.ItemDataRole.UserRole:
            return actor
        if role == Qt.ItemDataRole.DisplayRole and index.column() == 0:
            return actor.name
        class_style = get_class_style(actor.sub_type)
        if role == Qt.ItemDataRole.BackgroundRole:
            return QColor(class_style.background)
        if role == Qt.ItemDataRole.ForegroundRole:
            return QColor(class_style.foreground)
        return QVariant()

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> object:
        """Return horizontal column labels."""
        if (
            role == Qt.ItemDataRole.DisplayRole
            and orientation == Qt.Orientation.Horizontal
            and 0 <= section < len(self._HEADERS)
        ):
            return self._HEADERS[section]
        return QVariant()

    def set_participants(self, participants: Iterable[Actor]) -> None:
        """Replace all participant rows."""
        self.beginResetModel()
        self._participants = tuple(participants)
        self.endResetModel()

    def actor_at(self, row: int) -> Actor | None:
        """Return the Actor at a row, if present."""
        if 0 <= row < len(self._participants):
            return self._participants[row]
        return None
