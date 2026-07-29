"""Background report-loading worker."""

import logging

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from wcl_analyzer.app import ReportLoader

logger = logging.getLogger(__name__)


class ReportLoadWorker(QObject):
    """Load a report outside the GUI thread and emit its result."""

    loaded = pyqtSignal(object)
    failed = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, report_loader: ReportLoader, report_input: str) -> None:
        super().__init__()
        self._report_loader = report_loader
        self._report_input = report_input

    @pyqtSlot()
    def run(self) -> None:
        """Execute the blocking report load."""
        try:
            report = self._report_loader.load_report(self._report_input)
        except Exception as error:
            logger.exception("Failed to load WCL report")
            self.failed.emit(str(error) or error.__class__.__name__)
        else:
            self.loaded.emit(report)
        finally:
            self.finished.emit()
