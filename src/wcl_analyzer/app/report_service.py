"""Application flow for loading report metadata."""

from urllib.parse import urlsplit

from wcl_analyzer.app.errors import InvalidReportInputError
from wcl_analyzer.app.ports import ReportRepository
from wcl_analyzer.domain import Report

_WCL_HOST = "warcraftlogs.com"


def normalize_report_code(report_input: str) -> str:
    """Extract and validate a case-sensitive WCL report code.

    The input may be a report code or a Warcraft Logs report URL. Query
    parameters and URL fragments are intentionally ignored.
    """
    value = report_input.strip()
    if not value:
        raise InvalidReportInputError("report code or URL must not be empty")

    if "://" not in value and "/" not in value:
        return _validate_report_code(value)

    candidate_url = value if "://" in value else f"https://{value}"
    parsed_url = urlsplit(candidate_url)
    host = (parsed_url.hostname or "").lower()
    if host != _WCL_HOST and not host.endswith(f".{_WCL_HOST}"):
        raise InvalidReportInputError("report URL must use the warcraftlogs.com host")

    path_parts = [part for part in parsed_url.path.split("/") if part]
    if len(path_parts) < 2 or path_parts[0].lower() != "reports":
        raise InvalidReportInputError("report URL must contain /reports/{code}")

    return _validate_report_code(path_parts[1])


def _validate_report_code(report_code: str) -> str:
    """Validate a report code without changing its case."""
    if not report_code.isascii() or not report_code.isalnum():
        raise InvalidReportInputError(
            "report code must contain only ASCII letters and digits"
        )
    return report_code


class ReportService:
    """Coordinate report input normalization and report loading."""

    def __init__(self, repository: ReportRepository) -> None:
        self._repository = repository

    def load_report(self, report_input: str) -> Report:
        """Load report metadata for a code or Warcraft Logs URL."""
        report_code = normalize_report_code(report_input)
        return self._repository.get_report(report_code)
