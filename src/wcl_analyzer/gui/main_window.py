"""Main application window."""

from time import monotonic

from PyQt6.QtCore import Qt, QThread, QTimer
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from wcl_analyzer.app import (
    ApiRateLimitStatus,
    ReportLoader,
    ReportLoadResult,
)
from wcl_analyzer.domain import Fight
from wcl_analyzer.gui.workers import ReportLoadWorker


class MainWindow(QMainWindow):
    """Top-level window for the WRATH desktop application."""

    def __init__(self, report_loader: ReportLoader) -> None:
        super().__init__()
        self._report_loader = report_loader
        self._load_thread: QThread | None = None
        self._load_worker: ReportLoadWorker | None = None
        self._rate_limit_status: ApiRateLimitStatus | None = None
        self._rate_limit_captured_at: float | None = None

        self.setObjectName("mainWindow")
        self.setWindowTitle("WRATH")
        self.resize(960, 640)

        self.title_label = QLabel("WRATH")
        self.title_label.setObjectName("titleLabel")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.report_input = QLineEdit()
        self.report_input.setObjectName("reportInput")
        self.report_input.setPlaceholderText("WCL report URL 또는 code")
        self.report_input.returnPressed.connect(self.load_report)

        self.load_button = QPushButton("불러오기")
        self.load_button.setObjectName("loadButton")
        self.load_button.clicked.connect(self.load_report)

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.report_input)
        input_layout.addWidget(self.load_button)

        self.fight_combo = QComboBox()
        self.fight_combo.setObjectName("fightCombo")
        self.fight_combo.setEnabled(False)
        self.fight_combo.activated.connect(self.print_selected_fight)

        self.status_label = QLabel("WCL report URL 또는 code를 입력하세요.")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.rate_limit_label = QLabel("API 포인트: 조회 전")
        self.rate_limit_label.setObjectName("rateLimitLabel")
        self.rate_limit_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        layout = QVBoxLayout()
        layout.addWidget(self.title_label)
        layout.addWidget(self.rate_limit_label)
        layout.addLayout(input_layout)
        layout.addWidget(self.fight_combo)
        layout.addWidget(self.status_label)
        layout.addStretch(1)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self._status_timer = QTimer(self)
        self._status_timer.setInterval(1_000)
        self._status_timer.timeout.connect(self._update_rate_limit_status)
        self._status_timer.start()

    def load_report(self) -> None:
        """Start loading the entered report on a worker thread."""
        report_input = self.report_input.text().strip()
        if not report_input:
            self.status_label.setText("WCL report URL 또는 code를 입력하세요.")
            return
        if self._load_thread is not None:
            return

        self.load_button.setEnabled(False)
        self.report_input.setEnabled(False)
        self.fight_combo.clear()
        self.fight_combo.setEnabled(False)
        self.status_label.setText("리포트를 불러오는 중입니다...")

        thread = QThread(self)
        worker = ReportLoadWorker(self._report_loader, report_input)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.loaded.connect(self._show_report)
        worker.failed.connect(self._show_load_error)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._finish_report_load)

        self._load_thread = thread
        self._load_worker = worker
        thread.start()

    def _show_report(self, result_value: object) -> None:
        """Populate the fight selector from a loaded domain report."""
        if not isinstance(result_value, ReportLoadResult):
            self._show_load_error("올바르지 않은 리포트 데이터입니다.")
            return

        report = result_value.report
        self._rate_limit_status = result_value.rate_limit
        self._rate_limit_captured_at = (
            monotonic() if result_value.rate_limit is not None else None
        )

        self.fight_combo.blockSignals(True)
        self.fight_combo.clear()
        for fight in report.fights:
            self.fight_combo.addItem(self._format_fight(fight), userData=fight)
        self.fight_combo.blockSignals(False)

        has_fights = self.fight_combo.count() > 0
        self.fight_combo.setEnabled(has_fights)
        if has_fights:
            self.fight_combo.setCurrentIndex(0)
            self.status_label.setText(
                f"{report.title}: {len(report.fights)}개 전투"
            )
        else:
            self.status_label.setText(f"{report.title}: 전투가 없습니다.")
        self._update_rate_limit_status()

    def _show_load_error(self, message: str) -> None:
        """Display a report-loading failure without closing the application."""
        self.fight_combo.clear()
        self.fight_combo.setEnabled(False)
        self.status_label.setText(f"리포트 로드 실패: {message}")

    def _finish_report_load(self) -> None:
        """Restore controls after the worker thread has stopped."""
        self._load_thread = None
        self._load_worker = None
        self.load_button.setEnabled(True)
        self.report_input.setEnabled(True)

    def print_selected_fight(self, index: int) -> None:
        """Print the Fight selected by the user."""
        fight = self.fight_combo.itemData(index)
        if not isinstance(fight, Fight):
            return
        print(
            "Selected fight: "
            f"id={fight.id}, name={fight.name}, "
            f"start={fight.start_time_ms} ms, "
            f"end={fight.end_time_ms} ms, "
            f"duration={fight.duration_ms} ms"
        )

    def _update_rate_limit_status(self) -> None:
        """Refresh the local rate-limit countdown without an API request."""
        self.rate_limit_label.setText(self._format_rate_limit_status())

    def _format_rate_limit_status(self) -> str:
        status = self._rate_limit_status
        captured_at = self._rate_limit_captured_at
        if status is None or captured_at is None:
            return "API 포인트: 조회 전"

        elapsed_seconds = max(0, int(monotonic() - captured_at))
        reset_remaining = max(0, status.reset_in_seconds - elapsed_seconds)
        return (
            f"API 포인트: {status.points_remaining:,.1f} / "
            f"{status.limit_per_hour:,} · "
            f"초기화 {self._format_duration(reset_remaining)} 후"
        )

    @staticmethod
    def _format_duration(total_seconds: int) -> str:
        days, remainder = divmod(max(0, total_seconds), 86_400)
        hours, remainder = divmod(remainder, 3_600)
        minutes, seconds = divmod(remainder, 60)
        if days:
            return f"{days}일 {hours}시간 {minutes}분"
        if hours:
            return f"{hours}시간 {minutes}분 {seconds}초"
        if minutes:
            return f"{minutes}분 {seconds}초"
        return f"{seconds}초"

    @staticmethod
    def _format_fight(fight: Fight) -> str:
        duration_seconds = fight.duration_ms / 1_000
        return f"{fight.id}. {fight.name} ({duration_seconds:.1f}초)"
