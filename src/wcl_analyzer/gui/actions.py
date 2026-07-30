"""Reusable GUI command definitions."""

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QWidget


class AppActions:
    """Application actions shared by buttons, menus, and shortcuts."""

    def __init__(self, parent: QWidget) -> None:
        self.load_report = QAction("불러오기", parent)
        self.load_report.setObjectName("loadReportAction")
