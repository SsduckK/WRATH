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

## Source layout

```text
src/wcl_analyzer/
├── main.py          # Composition root and application entry point
├── gui/             # PyQt widgets and application startup
├── app/             # Application use cases and flow coordination
├── domain/          # Input-independent models and business rules
└── infrastructure/  # External APIs, files, databases, and caches
```
