"""Code-driven presentation settings for the WRATH GUI."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ClassStyle:
    """Foreground and background colors for a WoW class."""

    background: str
    foreground: str


WOW_CLASS_STYLES: dict[str, ClassStyle] = {
    "deathknight": ClassStyle("#C41E3A", "#FFFFFF"),
    "demonhunter": ClassStyle("#A330C9", "#FFFFFF"),
    "druid": ClassStyle("#FF7C0A", "#111111"),
    "evoker": ClassStyle("#33937F", "#FFFFFF"),
    "hunter": ClassStyle("#AAD372", "#111111"),
    "mage": ClassStyle("#3FC7EB", "#111111"),
    "monk": ClassStyle("#00FF98", "#111111"),
    "paladin": ClassStyle("#F48CBA", "#111111"),
    "priest": ClassStyle("#FFFFFF", "#111111"),
    "rogue": ClassStyle("#FFF468", "#111111"),
    "shaman": ClassStyle("#0070DD", "#FFFFFF"),
    "warlock": ClassStyle("#8788EE", "#111111"),
    "warrior": ClassStyle("#C69B6D", "#111111"),
}

DEFAULT_CLASS_STYLE = ClassStyle("#4B5563", "#FFFFFF")

DEFAULT_WINDOW_WIDTH = 960
DEFAULT_WINDOW_HEIGHT = 640
ANALYSIS_OUTPUT_AREA_WEIGHT = 80
PLAYER_FILTER_AREA_WEIGHT = 20
CONTENT_SPLITTER_HANDLE_WIDTH = 6
PARTICIPANT_ROW_HEIGHT = 34
PARTICIPANT_FONT_POINT_SIZE = 11


def get_class_style(class_name: str | None) -> ClassStyle:
    """Return a class style while tolerating spaces and unknown classes."""
    normalized_name = (class_name or "").replace(" ", "").lower()
    return WOW_CLASS_STYLES.get(normalized_name, DEFAULT_CLASS_STYLE)
