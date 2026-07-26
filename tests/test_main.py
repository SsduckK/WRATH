"""Tests for the application composition root."""

from wcl_analyzer import main as main_module


class FakeApplication:
    """Minimal QApplication replacement used by the entry-point test."""

    def __init__(self, exit_code: int) -> None:
        self.exit_code = exit_code
        self.exec_called = False

    def exec(self) -> int:
        self.exec_called = True
        return self.exit_code


class FakeWindow:
    """Minimal main-window replacement used by the entry-point test."""

    def __init__(self) -> None:
        self.show_called = False

    def show(self) -> None:
        self.show_called = True


def test_main_builds_and_runs_application(monkeypatch) -> None:
    application = FakeApplication(exit_code=7)
    window = FakeWindow()

    monkeypatch.setattr(main_module, "create_application", lambda argv: application)
    monkeypatch.setattr(main_module, "create_main_window", lambda: window)

    exit_code = main_module.main(["wrath"])

    assert window.show_called
    assert application.exec_called
    assert exit_code == 7
