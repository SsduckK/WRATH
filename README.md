# WRATH

Warcraft Real-time Analytics Tool Hub is a local desktop application for
analyzing Warcraft Logs reports and local combat logs.

## Development

The project requires Python 3.12 and uses `uv` for dependency management.

```bash
uv sync
uv run wrath
```

The GUI can also be started as a Python module.

```bash
uv run python -m wcl_analyzer
```

Run the tests with:

```bash
uv run pytest
```

## Checking a public WCL report

Create a Warcraft Logs v2 API client, then provide its credentials as
environment variables. Do not commit or log these values.

```bash
export WCL_CLIENT_ID='your-client-id'
export WCL_CLIENT_SECRET='your-client-secret'
uv run python scripts/check_wcl_report.py \
  'https://www.warcraftlogs.com/reports/REPORT_CODE'
```

The same environment variables are used by the GUI:

```bash
uv run wrath
```

Enter a report URL or code and select **불러오기**. Report loading runs on a
worker thread; the returned fights are shown in the fight selector. The GUI
also shows the latest WCL API point balance returned with the report query.
The reset countdown updates locally and does not make additional API requests.
Selecting a fight displays its friendly players in a table resolved from WCL
report master data. Clicking a player row prints the selected player name to
the development console. Player rows use the class information retained in the
domain model to apply WoW class colors. The report input, API point status,
fight selector, and load status are grouped at the top. The lower content is
split into a large analysis-output area on the left and a smaller player/filter
area on the right; code-driven presentation values are centralized in
`gui/gui_config.py`. Their initial ratio is 80:20, and the splitter handle can
be dragged to resize both areas. Clicking a player displays the known name and
class immediately, then loads only the selected fight's summary, damage,
healing, and death tables on a worker thread. The mapped result is cached per
fight. DPS is calculated as total damage divided by fight duration in seconds;
HPS is calculated from total healing using the same duration. WCL
report-relative death timestamps are normalized to elapsed fight time and
displayed as `MM.SS.mmm`. Fight durations use the same format; values WCL does
not provide are shown as `None`.

## Source layout

```text
src/wcl_analyzer/
├── main.py          # Composition root and application entry point
├── gui/             # PyQt widgets and application startup
├── app/             # Application use cases and flow coordination
├── domain/          # Input-independent models and business rules
└── infrastructure/  # External APIs, files, databases, and caches
```
