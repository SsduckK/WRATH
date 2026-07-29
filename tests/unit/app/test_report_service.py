"""Unit tests for the report-loading application flow."""

import pytest

from wcl_analyzer.app import (
    InvalidReportInputError,
    ReportService,
    normalize_report_code,
)
from wcl_analyzer.domain import Fight, Report


class FakeReportRepository:
    """In-memory repository used to isolate application-service tests."""

    def __init__(self, report: Report) -> None:
        self.report = report
        self.requested_codes: list[str] = []

    def get_report(self, report_code: str) -> Report:
        self.requested_codes.append(report_code)
        return self.report


@pytest.mark.parametrize(
    ("report_input", "expected_code"),
    [
        ("AbCd1234", "AbCd1234"),
        ("  AbCd1234  ", "AbCd1234"),
        (
            "https://www.warcraftlogs.com/reports/AbCd1234",
            "AbCd1234",
        ),
        (
            "https://www.warcraftlogs.com/reports/AbCd1234#fight=2",
            "AbCd1234",
        ),
        (
            "warcraftlogs.com/reports/AbCd1234?fight=last",
            "AbCd1234",
        ),
    ],
)
def test_normalize_report_code(
    report_input: str,
    expected_code: str,
) -> None:
    assert normalize_report_code(report_input) == expected_code


@pytest.mark.parametrize(
    "report_input",
    [
        "",
        "   ",
        "invalid-code!",
        "https://example.com/reports/AbCd1234",
        "https://www.warcraftlogs.com/rankings/AbCd1234",
        "https://www.warcraftlogs.com/reports/",
    ],
)
def test_normalize_report_code_rejects_invalid_input(report_input: str) -> None:
    with pytest.raises(InvalidReportInputError):
        normalize_report_code(report_input)


def test_load_report_normalizes_input_and_delegates_to_repository() -> None:
    report = Report(
        code="AbCd1234",
        title="Test Report",
        fights=(
            Fight(
                id=1,
                name="Test Encounter",
                start_time_ms=1_000,
                end_time_ms=4_500,
            ),
        ),
    )
    repository = FakeReportRepository(report)
    service = ReportService(repository)

    loaded_report = service.load_report(
        "https://www.warcraftlogs.com/reports/AbCd1234#fight=1"
    )

    assert loaded_report is report
    assert repository.requested_codes == ["AbCd1234"]
