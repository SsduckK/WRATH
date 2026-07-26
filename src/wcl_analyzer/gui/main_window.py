"""Main application window."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget


class MainWindow(QMainWindow):
    """Top-level window for the WRATH desktop application."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("mainWindow")
        self.setWindowTitle("WRATH")
        self.resize(960, 640)

        title_label = QLabel("WRATH")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        status_label = QLabel("Warcraft Logs 분석 도구를 준비하고 있습니다.")
        status_label.setObjectName("statusLabel")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout()
        layout.addStretch()
        layout.addWidget(title_label)
        layout.addWidget(status_label)
        layout.addStretch()

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
