"""Background loading for one fight's player aggregates."""

import logging

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from wcl_analyzer.app import ReportLoader
from wcl_analyzer.domain import Fight, Report

logger = logging.getLogger(__name__)


class FightStatsLoadWorker(QObject):
    """Load selected-fight aggregates outside the GUI thread."""

    loaded = pyqtSignal(object)
    failed = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(
        self,
        report_loader: ReportLoader,
        report: Report,
        fight: Fight,
    ) -> None:
        super().__init__()
        self._report_loader = report_loader
        self._report = report
        self._fight = fight

    @pyqtSlot()
    def run(self) -> None:
        """Execute the blocking aggregate-table request."""
        try:
            stats = self._report_loader.load_fight_player_stats(
                self._report,
                self._fight,
            )
        except Exception as error:
            logger.exception("Failed to load WCL fight player statistics")
            self.failed.emit(str(error) or error.__class__.__name__)
        else:
            self.loaded.emit(stats)
        finally:
            self.finished.emit()
