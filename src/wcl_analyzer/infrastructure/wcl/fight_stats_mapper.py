"""Map fight-scoped WCL table JSON into stable domain aggregates."""

from collections.abc import Iterable, Mapping
from math import isfinite

from wcl_analyzer.domain import Actor, Fight, FightPlayerStats, PlayerFightStats
from wcl_analyzer.infrastructure.wcl.mapper import WclMappingError


def map_fight_player_stats(
    payload: Mapping[str, object],
    report_code: str,
    fight: Fight,
    actors: Iterable[Actor],
) -> FightPlayerStats:
    """Map WCL JSON tables, tolerating unknown and optional fields."""
    report = _report(payload)
    summary = _all_entries(report.get("summary"), "composition", "entries")
    damage = _entries(report.get("damage"), "entries")
    healing = _entries(report.get("healing"), "entries")
    deaths = _entries(report.get("deaths"), "entries")

    summary_by_id = _by_actor_id(summary)
    damage_by_id = _by_actor_id(damage)
    healing_by_id = _by_actor_id(healing)
    deaths_by_id = _by_actor_id(deaths)
    duration_seconds = fight.duration_ms / 1_000

    results: list[PlayerFightStats] = []
    for actor in actors:
        raw_summary = summary_by_id.get(actor.id, {})
        damage_total = _non_negative_int(damage_by_id.get(actor.id, {}).get("total"))
        healing_total = _non_negative_int(healing_by_id.get(actor.id, {}).get("total"))
        results.append(
            PlayerFightStats(
                actor_id=actor.id,
                specialization=_specialization(raw_summary),
                item_level=_item_level(raw_summary),
                damage=damage_total,
                dps=(damage_total / duration_seconds if duration_seconds else 0.0),
                healing=healing_total,
                hps=(healing_total / duration_seconds if duration_seconds else 0.0),
                death_time_ms=_fight_relative_death_time(
                    deaths_by_id.get(actor.id, {}),
                    fight,
                ),
            )
        )
    return FightPlayerStats(
        report_code=report_code,
        fight_id=fight.id,
        players=tuple(results),
    )


def _report(payload: Mapping[str, object]) -> Mapping[str, object]:
    try:
        data = payload["data"]
        report_data = data["reportData"]  # type: ignore[index]
        report = report_data["report"]  # type: ignore[index]
    except (KeyError, TypeError) as error:
        raise WclMappingError("fight stats response is missing report data") from error
    if not isinstance(report, Mapping):
        raise WclMappingError("fight stats report must be an object")
    return report


def _entries(value: object, *keys: str) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, Mapping):
        return ()
    data = value.get("data", value)
    if not isinstance(data, Mapping):
        return ()
    raw_entries: object = ()
    for key in keys:
        candidate = data.get(key)
        if isinstance(candidate, list):
            raw_entries = candidate
            break
    if not isinstance(raw_entries, list):
        return ()
    return tuple(entry for entry in raw_entries if isinstance(entry, Mapping))


def _all_entries(value: object, *keys: str) -> tuple[Mapping[str, object], ...]:
    """Combine alternate lists when a WCL table exposes split metadata."""
    combined: list[Mapping[str, object]] = []
    for key in keys:
        combined.extend(_entries(value, key))
    return tuple(combined)


def _by_actor_id(
    entries: Iterable[Mapping[str, object]],
) -> dict[int, Mapping[str, object]]:
    result: dict[int, Mapping[str, object]] = {}
    for entry in entries:
        actor_id = entry.get("id", entry.get("actorID"))
        if isinstance(actor_id, int) and not isinstance(actor_id, bool):
            result[actor_id] = {**result.get(actor_id, {}), **entry}
    return result


def _specialization(entry: Mapping[str, object]) -> str | None:
    for key in ("spec", "specName"):
        value = entry.get(key)
        if isinstance(value, str) and value.strip():
            return value
    specs = entry.get("specs")
    if isinstance(specs, list) and specs:
        first = specs[0]
        if isinstance(first, str) and first.strip():
            return first
        if isinstance(first, Mapping):
            for key in ("name", "spec", "specialization"):
                name = first.get(key)
                if isinstance(name, str) and name.strip():
                    return name
    return None


def _item_level(entry: Mapping[str, object]) -> float | None:
    for key in ("itemLevel", "averageItemLevel", "maxItemLevel", "minItemLevel"):
        value = entry.get(key)
        number = _optional_non_negative_number(value)
        if number is not None:
            return number
    return None


def _death_time(entry: Mapping[str, object]) -> int | None:
    for key in ("deathTime", "timestamp"):
        value = entry.get(key)
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            return value
    deaths = entry.get("deaths")
    if isinstance(deaths, list):
        times = [
            time
            for death in deaths
            if isinstance(death, Mapping)
            for time in [_death_time(death)]
            if time is not None
        ]
        return min(times) if times else None
    return None


def _fight_relative_death_time(
    entry: Mapping[str, object],
    fight: Fight,
) -> int | None:
    """Convert a WCL report-relative death timestamp to fight elapsed time."""
    report_relative_ms = _death_time(entry)
    if report_relative_ms is None:
        return None
    elapsed_ms = report_relative_ms - fight.start_time_ms
    return elapsed_ms if elapsed_ms >= 0 else None


def _non_negative_int(value: object) -> int:
    return int(_non_negative_number(value))


def _non_negative_number(value: object) -> float:
    return _optional_non_negative_number(value) or 0.0


def _optional_non_negative_number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    number = float(value)
    return number if isfinite(number) and number >= 0 else None
