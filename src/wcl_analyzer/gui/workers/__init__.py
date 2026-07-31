"""Background workers used by the WRATH GUI."""

from wcl_analyzer.gui.workers.fight_stats_loader import FightStatsLoadWorker
from wcl_analyzer.gui.workers.report_loader import ReportLoadWorker

__all__ = ["FightStatsLoadWorker", "ReportLoadWorker"]
