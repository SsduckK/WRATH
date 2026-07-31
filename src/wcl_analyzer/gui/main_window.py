"""Main application window."""

from time import monotonic

from PyQt6.QtCore import Qt, QThread, QTimer
from PyQt6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from wcl_analyzer.app import (
    ApiRateLimitStatus,
    ReportLoader,
    ReportLoadResult,
)
from wcl_analyzer.domain import (
    Actor,
    Fight,
    FightPlayerStats,
    PlayerFightStats,
    Report,
)
from wcl_analyzer.gui.actions import AppActions
from wcl_analyzer.gui.formatters import format_elapsed_ms
from wcl_analyzer.gui.gui_config import (
    ANALYSIS_OUTPUT_AREA_WEIGHT,
    CONTENT_SPLITTER_HANDLE_WIDTH,
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    PLAYER_FILTER_AREA_WEIGHT,
)
from wcl_analyzer.gui.widgets import (
    AppButton,
    FightSelector,
    ParticipantTableView,
)
from wcl_analyzer.gui.workers import FightStatsLoadWorker, ReportLoadWorker


class MainWindow(QMainWindow):
    """Top-level window for the WRATH desktop application."""

    def __init__(self, report_loader: ReportLoader) -> None:
        super().__init__()
        self._report_loader = report_loader
        self._load_thread: QThread | None = None
        self._load_worker: ReportLoadWorker | None = None
        self._stats_thread: QThread | None = None
        self._stats_worker: FightStatsLoadWorker | None = None
        self._loading_stats_key: tuple[str, int] | None = None
        self._current_report: Report | None = None
        self._current_fight: Fight | None = None
        self._selected_actor: Actor | None = None
        self._fight_stats_cache: dict[tuple[str, int], FightPlayerStats] = {}
        self._rate_limit_status: ApiRateLimitStatus | None = None
        self._rate_limit_captured_at: float | None = None

        self.setObjectName("mainWindow")
        self.setWindowTitle("WRATH")
        self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)

        self.actions = AppActions(self)
        self.actions.load_report.triggered.connect(self.load_report)

        self.report_input = QLineEdit()
        self.report_input.setObjectName("reportInput")
        self.report_input.setPlaceholderText("WCL report URL 또는 code")
        self.report_input.returnPressed.connect(self.actions.load_report.trigger)

        self.load_button = AppButton(
            self.actions.load_report,
            object_name="loadButton",
        )

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.report_input)
        input_layout.addWidget(self.load_button)

        self.fight_combo = FightSelector()
        self.fight_combo.fight_selected.connect(self.print_selected_fight)

        self.participant_table = ParticipantTableView()
        self.participant_table.player_clicked.connect(self.show_clicked_player)

        self.status_label = QLabel("WCL report URL 또는 code를 입력하세요.")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.rate_limit_label = QLabel("API 포인트: 조회 전")
        self.rate_limit_label.setObjectName("rateLimitLabel")
        self.rate_limit_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        report_load_area = QGroupBox("로그 불러오기")
        report_load_area.setObjectName("reportLoadArea")
        report_load_layout = QVBoxLayout(report_load_area)
        report_load_layout.addLayout(input_layout)
        report_load_layout.addWidget(self.rate_limit_label)
        report_load_layout.addWidget(self.fight_combo)
        report_load_layout.addWidget(self.status_label)

        self.interaction_output_area = QFrame()
        self.interaction_output_area.setObjectName("interactionOutputArea")
        self.interaction_output_area.setFrameShape(QFrame.Shape.StyledPanel)
        self.interaction_output_layout = QVBoxLayout(self.interaction_output_area)
        self.player_detail_label = QLabel("플레이어를 선택하세요.")
        self.player_detail_label.setObjectName("playerDetailLabel")
        self.player_detail_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )
        self.player_detail_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.player_detail_label.setWordWrap(True)
        self.interaction_output_layout.addWidget(self.player_detail_label)
        self.interaction_output_layout.addStretch(1)

        self.player_filter_area = QFrame()
        self.player_filter_area.setObjectName("playerFilterArea")
        self.player_filter_area.setFrameShape(QFrame.Shape.StyledPanel)
        player_filter_layout = QVBoxLayout(self.player_filter_area)
        player_filter_layout.addWidget(self.participant_table)

        self.content_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.content_splitter.setObjectName("contentSplitter")
        self.content_splitter.addWidget(self.interaction_output_area)
        self.content_splitter.addWidget(self.player_filter_area)
        self.content_splitter.setChildrenCollapsible(False)
        self.content_splitter.setHandleWidth(CONTENT_SPLITTER_HANDLE_WIDTH)
        self.content_splitter.setStretchFactor(
            0,
            ANALYSIS_OUTPUT_AREA_WEIGHT,
        )
        self.content_splitter.setStretchFactor(
            1,
            PLAYER_FILTER_AREA_WEIGHT,
        )
        total_area_weight = ANALYSIS_OUTPUT_AREA_WEIGHT + PLAYER_FILTER_AREA_WEIGHT
        self.content_splitter.setSizes(
            [
                DEFAULT_WINDOW_WIDTH * ANALYSIS_OUTPUT_AREA_WEIGHT // total_area_weight,
                DEFAULT_WINDOW_WIDTH * PLAYER_FILTER_AREA_WEIGHT // total_area_weight,
            ]
        )

        layout = QVBoxLayout()
        layout.addWidget(report_load_area)
        layout.addWidget(self.content_splitter, 1)

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

        self.actions.load_report.setEnabled(False)
        self.report_input.setEnabled(False)
        self.fight_combo.clear_fights()
        self.participant_table.clear_participants()
        self._current_fight = None
        self._selected_actor = None
        self._fight_stats_cache.clear()
        self._clear_player_details()
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
        self._current_report = report
        self._rate_limit_status = result_value.rate_limit
        self._rate_limit_captured_at = (
            monotonic() if result_value.rate_limit is not None else None
        )

        self.fight_combo.set_fights(report.fights)
        has_fights = bool(report.fights)
        if has_fights:
            self._show_fight_participants(report.fights[0])
            self.status_label.setText(f"{report.title}: {len(report.fights)}개 전투")
        else:
            self.participant_table.clear_participants()
            self.status_label.setText(f"{report.title}: 전투가 없습니다.")
        self._update_rate_limit_status()

    def _show_load_error(self, message: str) -> None:
        """Display a report-loading failure without closing the application."""
        self._current_report = None
        self._current_fight = None
        self._selected_actor = None
        self._fight_stats_cache.clear()
        self.fight_combo.clear_fights()
        self.participant_table.clear_participants()
        self._clear_player_details()
        self.status_label.setText(f"리포트 로드 실패: {message}")

    def _finish_report_load(self) -> None:
        """Restore controls after the worker thread has stopped."""
        self._load_thread = None
        self._load_worker = None
        self.actions.load_report.setEnabled(True)
        self.report_input.setEnabled(True)

    def print_selected_fight(self, fight_value: object) -> None:
        """Print the selected Fight and its friendly player list."""
        if not isinstance(fight_value, Fight):
            return
        fight = fight_value
        participants = self._show_fight_participants(fight)
        print(
            "Selected fight: "
            f"id={fight.id}, name={fight.name}, "
            f"start={fight.start_time_ms} ms, "
            f"end={fight.end_time_ms} ms, "
            f"duration={fight.duration_ms} ms"
        )
        print(f"Participants ({len(participants)}):")
        for actor in participants:
            detail = f" · {actor.sub_type}" if actor.sub_type else ""
            print(f"- {actor.name} (report actor id={actor.id}{detail})")

    def _show_fight_participants(self, fight: Fight) -> tuple[Actor, ...]:
        """Resolve and display the selected fight's friendly players."""
        participants = (
            self._current_report.get_fight_participants(fight)
            if self._current_report is not None
            else ()
        )
        self.participant_table.set_participants(participants)
        self._current_fight = fight
        self._selected_actor = None
        self._clear_player_details()
        return participants

    def show_clicked_player(self, player_value: object) -> None:
        """Load and display the clicked player's selected-fight statistics."""
        if not isinstance(player_value, Actor):
            return
        self._selected_actor = player_value
        print(f"player{{{player_value.name}}} clicked")

        report = self._current_report
        fight = self._current_fight
        if report is None or fight is None:
            self._display_player_details(player_value, None)
            return

        cached = self._fight_stats_cache.get((report.code, fight.id))
        if cached is not None:
            self._display_player_details(
                player_value,
                cached.get_player(player_value.id),
            )
            return

        self.player_detail_label.setText("플레이어 통계를 불러오는 중입니다...")
        if self._stats_thread is None:
            self._start_fight_stats_load(report, fight)

    def _start_fight_stats_load(self, report: Report, fight: Fight) -> None:
        """Start one fight-scoped WCL table request on a worker thread."""
        thread = QThread(self)
        worker = FightStatsLoadWorker(self._report_loader, report, fight)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.loaded.connect(self._show_fight_stats)
        worker.failed.connect(self._show_fight_stats_error)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._finish_fight_stats_load)
        self._stats_thread = thread
        self._stats_worker = worker
        self._loading_stats_key = (report.code, fight.id)
        thread.start()

    def _show_fight_stats(self, stats_value: object) -> None:
        """Cache loaded fight aggregates and refresh the selected player."""
        if not isinstance(stats_value, FightPlayerStats):
            self._show_fight_stats_error("올바르지 않은 전투 통계입니다.")
            return
        self._fight_stats_cache[(stats_value.report_code, stats_value.fight_id)] = (
            stats_value
        )
        report = self._current_report
        fight = self._current_fight
        actor = self._selected_actor
        if (
            report is not None
            and fight is not None
            and actor is not None
            and report.code == stats_value.report_code
            and fight.id == stats_value.fight_id
        ):
            self._display_player_details(
                actor,
                stats_value.get_player(actor.id),
            )

    def _show_fight_stats_error(self, message: str) -> None:
        """Present an aggregate request failure in the output area."""
        self.player_detail_label.setText(f"플레이어 통계 로드 실패: {message}")

    def _finish_fight_stats_load(self) -> None:
        """Release the completed worker and load a newly selected fight."""
        completed_key = self._loading_stats_key
        self._stats_thread = None
        self._stats_worker = None
        self._loading_stats_key = None
        report = self._current_report
        fight = self._current_fight
        actor = self._selected_actor
        if report is None or fight is None or actor is None:
            return
        current_key = (report.code, fight.id)
        if current_key != completed_key and current_key not in self._fight_stats_cache:
            self._start_fight_stats_load(report, fight)

    def _display_player_details(
        self,
        actor: Actor,
        stats: object,
    ) -> None:
        """Render known identity and optional fight aggregates."""
        if not isinstance(stats, PlayerFightStats):
            specialization = item_level = damage = dps = "None"
            healing = hps = death_time = "None"
        else:
            specialization = stats.specialization or "None"
            item_level = (
                f"{stats.item_level:,.1f}" if stats.item_level is not None else "None"
            )
            damage = f"{stats.damage:,}"
            dps = f"{stats.dps:,.1f}"
            healing = f"{stats.healing:,}"
            hps = f"{stats.hps:,.1f}"
            death_time = format_elapsed_ms(stats.death_time_ms)
        player_class = actor.sub_type or "None"
        self.player_detail_label.setText(
            f"name: {actor.name},  class: {player_class}-{specialization}, "
            f"item level: {item_level}\n"
            f"Damage: {damage}, DPS: {dps}\n"
            f"Healing: {healing}, HPS: {hps}\n"
            f"Death Time: {death_time}"
        )

    def _clear_player_details(self) -> None:
        """Reset the output when its report or fight context changes."""
        self.player_detail_label.setText("플레이어를 선택하세요.")

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
