"""Load one public WCL report without starting the GUI."""

import argparse

from wcl_analyzer.app import ReportService
from wcl_analyzer.infrastructure.wcl import (
    WclGraphqlClient,
    WclReportRepository,
    WclTokenProvider,
)


def main() -> int:
    """Load and print report metadata using environment credentials."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", help="WCL report code or report URL")
    arguments = parser.parse_args()

    token_provider = WclTokenProvider.from_environment()
    client = WclGraphqlClient(token_provider)
    repository = WclReportRepository(client)
    service = ReportService(repository)
    report = service.load_report(arguments.report)

    print(f"Report: {report.title} ({report.code})")
    for fight in report.fights:
        print(
            f"{fight.id}: {fight.name} "
            f"[{fight.start_time_ms}-{fight.end_time_ms} ms, "
            f"duration={fight.duration_ms} ms]"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
