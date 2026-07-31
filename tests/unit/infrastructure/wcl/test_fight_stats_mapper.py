"""Tests for mapping WCL fight table JSON."""

import pytest

from wcl_analyzer.domain import Actor, Fight
from wcl_analyzer.infrastructure.wcl.fight_stats_mapper import (
    map_fight_player_stats,
)


def test_maps_player_tables_and_calculates_dps_from_fight_duration() -> None:
    fight = Fight(
        id=7,
        name="Encounter",
        start_time_ms=10_000,
        end_time_ms=110_000,
        friendly_actor_ids=(101,),
    )
    actor = Actor(101, "Alpha", "Player", "Warrior")
    payload = {
        "data": {
            "reportData": {
                "report": {
                    "summary": {
                        "data": {
                            "composition": [
                                {
                                    "id": 101,
                                    "specs": ["Arms"],
                                    "itemLevel": 630.25,
                                }
                            ]
                        }
                    },
                    "damage": {"data": {"entries": [{"id": 101, "total": 1_250_000}]}},
                    "healing": {"data": {"entries": [{"id": 101, "total": 25_000}]}},
                    "deaths": {
                        "data": {
                            "entries": [{"id": 101, "deaths": [{"deathTime": 95_000}]}]
                        }
                    },
                }
            }
        }
    }

    result = map_fight_player_stats(payload, "Report123", fight, (actor,))
    stats = result.get_player(101)

    assert result.report_code == "Report123"
    assert result.fight_id == 7
    assert stats is not None
    assert stats.specialization == "Arms"
    assert stats.item_level == pytest.approx(630.25)
    assert stats.damage == 1_250_000
    assert stats.dps == pytest.approx(12_500.0)
    assert stats.healing == 25_000
    assert stats.hps == pytest.approx(250.0)
    assert stats.death_time_ms == 85_000


def test_missing_optional_table_values_are_explicit_defaults() -> None:
    fight = Fight(1, "Encounter", 0, 0, (101,))
    actor = Actor(101, "Alpha", "Player", "Warrior")
    payload = {"data": {"reportData": {"report": {}}}}

    result = map_fight_player_stats(payload, "Report123", fight, (actor,))
    stats = result.get_player(101)

    assert stats is not None
    assert stats.specialization is None
    assert stats.item_level is None
    assert stats.damage == 0
    assert stats.dps == 0
    assert stats.healing == 0
    assert stats.hps == 0
    assert stats.death_time_ms is None
