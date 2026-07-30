"""Map Warcraft Logs GraphQL payloads to domain models."""

from collections.abc import Mapping
from math import isfinite
from typing import Never

from wcl_analyzer.domain import Actor, Fight, Report


class WclMappingError(ValueError):
    """Raised when a WCL response lacks required or valid fields."""


def map_report_response(payload: Mapping[str, object]) -> Report:
    """Map a WCL report query response to a domain ``Report``.

    Expected GraphQL shape:
    ``data.reportData.report.{code,title,fights}``.
    Unknown response fields are intentionally ignored.
    """
    if payload.get("errors"):
        raise WclMappingError("GraphQL response contains errors")

    data = _required_mapping(payload, "data", "response")
    report_data = _required_mapping(data, "reportData", "data")
    raw_report = _required_mapping(report_data, "report", "data.reportData")

    code = _required_string(raw_report, "code", "report")
    title = _required_string(raw_report, "title", "report")
    raw_fights = _required_list(raw_report, "fights", "report")
    actors = _map_actors(raw_report)

    fights = tuple(
        _map_fight(_as_mapping(raw_fight, f"report.fights[{index}]"))
        for index, raw_fight in enumerate(raw_fights)
    )

    try:
        return Report(code=code, title=title, fights=fights, actors=actors)
    except ValueError as error:
        raise WclMappingError(f"invalid report data: {error}") from error


def _map_fight(raw_fight: Mapping[str, object]) -> Fight:
    fight_id = _required_int(raw_fight, "id", "fight")
    name = _required_string(raw_fight, "name", "fight")
    start_time_ms = _required_millisecond(raw_fight, "startTime", "fight")
    end_time_ms = _required_millisecond(raw_fight, "endTime", "fight")
    friendly_actor_ids = _optional_int_tuple(
        raw_fight,
        "friendlyPlayers",
        "fight",
    )

    try:
        return Fight(
            id=fight_id,
            name=name,
            start_time_ms=start_time_ms,
            end_time_ms=end_time_ms,
            friendly_actor_ids=friendly_actor_ids,
        )
    except ValueError as error:
        raise WclMappingError(f"invalid fight data: {error}") from error


def _map_actors(raw_report: Mapping[str, object]) -> tuple[Actor, ...]:
    raw_master_data = raw_report.get("masterData")
    if raw_master_data is None:
        return ()
    master_data = _as_mapping(raw_master_data, "report.masterData")
    raw_actors = master_data.get("actors")
    if raw_actors is None:
        return ()
    if not isinstance(raw_actors, list):
        raise WclMappingError("report.masterData.actors must be a list")

    actors: list[Actor] = []
    for index, raw_actor_value in enumerate(raw_actors):
        raw_actor = _as_mapping(
            raw_actor_value,
            f"report.masterData.actors[{index}]",
        )
        actor_id = _required_int(raw_actor, "id", "actor")
        name = _required_string(raw_actor, "name", "actor")
        actor_type = _optional_string(raw_actor, "type") or "Unknown"
        sub_type = _optional_string(raw_actor, "subType")
        try:
            actors.append(
                Actor(
                    id=actor_id,
                    name=name,
                    actor_type=actor_type,
                    sub_type=sub_type,
                )
            )
        except ValueError as error:
            raise WclMappingError(f"invalid actor data: {error}") from error
    return tuple(actors)


def _required_mapping(
    container: Mapping[str, object],
    field: str,
    location: str,
) -> Mapping[str, object]:
    return _as_mapping(_required_value(container, field, location), f"{location}.{field}")


def _as_mapping(value: object, location: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise WclMappingError(f"{location} must be an object")
    return value


def _required_list(
    container: Mapping[str, object],
    field: str,
    location: str,
) -> list[object]:
    value = _required_value(container, field, location)
    if not isinstance(value, list):
        raise WclMappingError(f"{location}.{field} must be a list")
    return value


def _required_string(
    container: Mapping[str, object],
    field: str,
    location: str,
) -> str:
    value = _required_value(container, field, location)
    if not isinstance(value, str):
        raise WclMappingError(f"{location}.{field} must be a string")
    return value


def _required_int(
    container: Mapping[str, object],
    field: str,
    location: str,
) -> int:
    value = _required_value(container, field, location)
    if isinstance(value, bool) or not isinstance(value, int):
        raise WclMappingError(f"{location}.{field} must be an integer")
    return value


def _required_millisecond(
    container: Mapping[str, object],
    field: str,
    location: str,
) -> int:
    value = _required_value(container, field, location)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise WclMappingError(f"{location}.{field} must be a number")
    if not isfinite(value) or not float(value).is_integer():
        raise WclMappingError(
            f"{location}.{field} must be a whole millisecond value"
        )
    return int(value)


def _optional_int_tuple(
    container: Mapping[str, object],
    field: str,
    location: str,
) -> tuple[int, ...]:
    value = container.get(field)
    if value is None:
        return ()
    if not isinstance(value, list):
        raise WclMappingError(f"{location}.{field} must be a list")

    values: list[int] = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, int):
            raise WclMappingError(
                f"{location}.{field} must contain only integers"
            )
        values.append(item)
    return tuple(values)


def _optional_string(
    container: Mapping[str, object],
    field: str,
) -> str | None:
    value = container.get(field)
    if value is None:
        return None
    if not isinstance(value, str):
        raise WclMappingError(f"{field} must be a string or null")
    return value


def _required_value(
    container: Mapping[str, object],
    field: str,
    location: str,
) -> object:
    if field not in container or container[field] is None:
        _raise_missing_field(f"{location}.{field}")
    return container[field]


def _raise_missing_field(location: str) -> Never:
    raise WclMappingError(f"required field is missing: {location}")
