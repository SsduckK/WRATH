"""Core domain models shared by every combat-data source."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Fight:
    """A fight time range within a report.

    ``start_time_ms`` and ``end_time_ms`` are report-relative milliseconds,
    not Unix timestamps.
    """

    id: int
    name: str
    start_time_ms: int
    end_time_ms: int

    def __post_init__(self) -> None:
        """Validate the fight's required identity and time range."""
        if self.id <= 0:
            raise ValueError("fight id must be greater than zero")
        if not self.name.strip():
            raise ValueError("fight name must not be empty")
        if self.start_time_ms < 0:
            raise ValueError("fight start_time_ms must not be negative")
        if self.end_time_ms < self.start_time_ms:
            raise ValueError(
                "fight end_time_ms must be greater than or equal to start_time_ms"
            )

    @property
    def duration_ms(self) -> int:
        """Return the fight duration in milliseconds."""
        return self.end_time_ms - self.start_time_ms


@dataclass(frozen=True, slots=True)
class Report:
    """A report and the fights available within it."""

    code: str
    title: str
    fights: tuple[Fight, ...] = ()

    def __post_init__(self) -> None:
        """Validate required report fields and fight identities."""
        if not self.code.strip():
            raise ValueError("report code must not be empty")
        if not self.title.strip():
            raise ValueError("report title must not be empty")

        fight_ids = [fight.id for fight in self.fights]
        if len(fight_ids) != len(set(fight_ids)):
            raise ValueError("fight ids must be unique within a report")

    def get_fight(self, fight_id: int) -> Fight | None:
        """Return a fight by report-local ID, if it exists."""
        return next((fight for fight in self.fights if fight.id == fight_id), None)
