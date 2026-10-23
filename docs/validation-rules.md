# GTFS Pathways validation rules

What this service checks in an uploaded GTFS feed, and what fails the upload. The Workspaces pathways editor
(workspaces-frontend) runs most of the same TDEI checks with the same rules and severities, so a feed edited there
shows the same problems before it's uploaded.

The checks themselves are in [src/custom_checks.py](../src/custom_checks.py); each one's docstring states its rule.
`test_custom_checks.py` checks that this page lists every check with its current severity.

## What fails an upload

There are two modes, set by `PATHWAYS_STRICT` (see the [README](../README.md#getting-started)) or
`scripts/validate_feed.py --strict`. Each report's `summary.strict` says which one it used.

**Lenient (the default, for now):** a feed fails only if it can't be read, or its core GTFS is broken. Problems in
pathways data are each local to one station, and rejecting the whole feed would lose every other station's good data,
so they're reported but don't fail it. A feed fails if it has any:

- **Unreadable feed:** MobilityData couldn't load it (e.g. it isn't a zip).
- **Core MobilityData error:** an `ERROR` from [MobilityData's GTFS validator](https://github.com/MobilityData/gtfs-validator)
  (version 8.0.1) that isn't in pathways data, except the codes [pathways_config.py](../src/pathways_config.py)
  downgrades to warnings (`CHANGE_ERROR_TO_WARNING`).

Pathways data (see [src/pathway_errors.py](../src/pathway_errors.py) and `pathways_config.py`) is TDEI's checks below;
MobilityData's pathway codes (`MOBILITY_DATA_PATHWAY_CODES`: e.g. unreachable locations, two-way exit gates, elevator
ends without a level); and any other MobilityData error in `pathways.txt` or `levels.txt`, or about an entrance,
generic node or boarding area. A MobilityData notice with problems both in and outside pathways data is split. Errors
in pathways data are reported as `downgraded_to_warning`, with `pathwayData` on the notice.

**Strict:** errors in pathways data fail the feed too: MobilityData's, and TDEI's checks with severity ERROR (those
that would route riders wrongly or not at all). The plan is to move to strict as agencies' pathways data improves.

In either mode, MobilityData's `pathway_unreachable_location` isn't an error for a place that's one-way by design
(see [src/one_way_service.py](../src/one_way_service.py)). A platform is **arrival-only** if every trip stopping
there ends there, or no stop time there allows pickup (`pickup_type` 1), and **departure-only** if every trip starts
there, or none allows drop-off (`drop_off_type` 1). An arrival-only platform's boarding areas, and the nodes on routes
from it, only need a way out; a departure-only one's, and the nodes on routes to it, only a way in. Those are reported
as `downgraded_to_warning`, with `oneWayService` on each sample; anything else unreachable is still an error,
including a place cut off both ways.

Warnings and info never fail an upload. Everything found is listed in the validation report (see the
[README](../README.md#validation-report)).

## Definitions

- **Station:** a stop with `location_type` 1. Its stops are those whose `parent_station` is the station, or a
  platform in it (for boarding areas).
- **Station with pathways:** a station with at least one stop that a pathway touches. Checks that need pathways
  skip other stations; riders reach their stops from the street.
- **Platform:** a stop with `location_type` 0 (or empty). A platform with boarding areas is reached through them.
- **Route:** a pathway goes from `from_stop_id` to `to_stop_id`, and back only if `is_bidirectional` is 1. Routes
  start or end at any entrance (`location_type` 2), in any station.
- **Step-free:** using only walkways, elevators, fare gates and exit gates (`pathway_mode` 1, 5, 6, 7): no stairs,
  moving sidewalks or escalators.
- **Distance:** GTFS has no pathway geometry, so distances are the straight line between stops' `stop_lat` and
  `stop_lon`. Checks that need one skip stops without coordinates.

## TDEI checks

The Editor column shows which checks the Workspaces editor also runs, with the same severities. There, a problem
that would fail the upload shows as a warning starting "Fails TDEI upload:" (a Rapid error would block saving work in
progress), INFO shows as a suggestion, and the editor's `TDEI_STRICT` (in `services/gtfs-severity.ts`) matches this
service's mode.

### ERROR: riders would be routed wrongly, or not at all (fails the upload in strict mode)

| Code | Rule | Editor |
|---|---|---|
| `tdei_level_unreachable` | A level a station with pathways uses, where none of the station's stops on it can be reached from an entrance | ✓ |
| `tdei_station_without_entrance` | A station with pathways that has no entrance | ✓ |

### WARNING: likely wrong; should be fixed

| Code | Rule | Editor |
|---|---|---|
| `tdei_level_change_same_level` | An escalator or elevator whose two stops have the same `level_id` | ✓ |
| `tdei_boarding_area_level` | A boarding area whose `level_id` differs from its platform's | ✓ |
| `tdei_stop_without_pathway` | A stop in a station with pathways that no pathway touches (not the station itself, or a platform with boarding areas) | ✓ |
| `tdei_entrance_without_location` | An entrance with no `stop_lat` or `stop_lon`, so outdoor (sidewalk) data can't connect to it | (can't happen there) |
| `tdei_stairs_same_level` | Stairs whose two stops have the same `level_id`, unless `stair_count` is under 10 (a short flight within the level) | ✓ |
| `tdei_escalator_two_way` | An escalator with `is_bidirectional` 1 | ✓ |
| `tdei_walkway_changes_level` | A walkway, moving sidewalk or gate between levels at different heights (`level_index`), with no `max_slope` (a ramp would have one) | ✓ |
| `tdei_stair_count_direction` | Stairs whose `stair_count` sign doesn't match the direction: positive should go up | ✓ |
| `tdei_length_too_short` | A walkway, moving sidewalk or gate whose `length` is under half the straight line between its stops, and at least 10 m off; skipped when either end is a platform or boarding area (an area placed at one point) | ✓ |
| `tdei_traversal_time_mismatch` | An escalator or moving sidewalk whose speed (`length`, or else the straight line, over `traversal_time`) is under 0.1 or over 5 m/s | ✓ |
| `tdei_duplicate_pathway` | A second pathway of the same mode joining the same two stops the same way, with lengths within 10% when both have one | ✓ |
| `tdei_pathway_ends_far_apart` | A pathway whose stops are farther apart than its mode spans: 500 m for walkways and moving sidewalks, 150 m for stairs and escalators, 50 m for elevators and gates | ✓ |
| `tdei_empty_level` | A level in `levels.txt` that no stop uses | ✓ |
| `tdei_level_index_repeated` | A station with two levels that have the same `level_index` (GTFS allows it, e.g. separate street and median levels) | ✓ |
| `tdei_level_index_far_from_street` | A station whose levels' `level_index` are all more than 20 from 0 (street level) | ✓ |
| `tdei_stop_far_from_level` | A stop 500 m or more from the middle (median) of the other stops on its level in its station (levels with 3 or more stops with coordinates) | ✓ |
| `tdei_missing_level_id` | A platform, generic node or boarding area with no `level_id`, in a station that uses levels | ✓ |
| `tdei_stop_far_from_station` | A stop more than 500 m from its station | ✓ |
| `tdei_entrance_reaches_no_platform` | An entrance in a station with pathways cut off from the platforms both ways: none can be reached from it, or reach it (an exit-only door is fine) | |

### INFO: worth a look; often correct

| Code | Rule | Editor |
|---|---|---|
| `tdei_length_too_long` | A walkway, moving sidewalk or gate whose `length` is over twice the straight line between its stops, and at least 10 m off; usually a winding route | ✓ |
| `tdei_entrance_reaches_no_platform_step_free` | An entrance from which platforms can be reached, but none step-free | |
| `tdei_platform_no_step_free_route_in` | A platform or boarding area that entrances reach, but none step-free | ✓ |
| `tdei_platform_no_step_free_exit` | A platform or boarding area that can reach an entrance, but none step-free | |
| `tdei_elevator_only_route` | A platform or boarding area whose only step-free route from an entrance goes through an elevator | ✓ |
| `tdei_no_step_free_transfer` | Two platforms in one station joined inside it, but not step-free, in one direction or both (platforms joined only through entrances are skipped) | |
| `tdei_entrance_not_street_level` | An entrance whose level's `level_index` isn't 0 | |
| `tdei_stops_share_location` | A walkway, moving sidewalk or gate whose stops are under 1 m apart but whose `length` is 10 m or more: one stop's coordinates are likely copied (the length checks skip stops this close) | ✓ |
| `tdei_stops_share_position` | Stops in a station on the same level at the same coordinates (to about 0.1 m), unless a fare gate, exit gate or elevator joins them: often a placeholder or duplicate (directional platforms sharing an island may be fine) | ✓ |
| `tdei_stairs_short_within_level` | Stairs whose two stops have the same `level_id`, with a `stair_count` of 1-9: a short flight within the level (not flagged as `tdei_stairs_same_level`) | ✓ |
| `tdei_entrance_exit_only` | An entrance riders can only leave through: no platform can be reached from it, but platforms reach it (not flagged as `tdei_entrance_reaches_no_platform`) | |
| `tdei_station_without_pathways` | A station none of whose stops a pathway touches; checks that need pathways skip it | |

## Already checked by MobilityData

TDEI doesn't repeat these; MobilityData's codes, with their own severities, are in brackets. Except for missing
names on platforms and stations, and duplicate or missing stop_ids for them, they're pathways data, so in lenient mode
their errors don't fail an upload. The Workspaces editor checks them too, the same way.

- Unreachable from an entrance, or no way back to one [`pathway_unreachable_location`, ERROR]
- Two-way exit gate [`bidirectional_exit_gate`, ERROR]
- Pathway ending at a station [`pathway_to_wrong_location_type`, ERROR]
- Pathway ending at a platform with boarding areas [`pathway_to_platform_with_boarding_areas`, ERROR]
- Pathway starting and ending at the same stop [`pathway_loop`, WARNING]
- Pathway to a stop riders reach from the street [`pathway_to_stop_with_access_outside_of_station_pathways`, ERROR]
- Elevator end without a `level_id` [`missing_level_id`, ERROR]
- Generic node only one pathway reaches [`pathway_dangling_generic_node`, WARNING]
- Duplicate `stop_id` or `pathway_id` [`duplicate_key`, ERROR]
- `parent_station`, `level_id`, `from_stop_id` or `to_stop_id` not found [`foreign_key_violation`, ERROR]
- `parent_station` of the wrong type [`wrong_parent_location_type`, ERROR], or missing
  [`location_without_parent_station`, ERROR]
- Missing `stop_name`, `pathway_mode`, `is_bidirectional` or `level_index` [`missing_stop_name`,
  `missing_required_field`, ERROR]
- Station no stop belongs to [`unused_station`, INFO]

## Metrics

Each report also measures the feed's stations (see [src/pathways_metrics.py](../src/pathways_metrics.py)), using the
same definitions: completeness (stations with pathways; stops with `level_id` and `wheelchair_boarding`; pathways with
`length` and `traversal_time`) and step-free connectivity (platforms with a step-free way in and out, entrances that
reach a platform step-free, and stations where every platform is step-free).
