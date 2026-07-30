"""Common WRATH widget classes."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QPushButton, QWidget


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
