# in an effort to be more permissive of small errors, accept these which could conceivably be calculated/fixed/interpreted by common applications
CHANGE_ERROR_TO_WARNING = [
    'block_trips_with_overlapping_stop_times',
    'trip_distance_exceeds_shape_distance',
    'decreasing_or_equal_stop_time_distance',
    'decreasing_shape_distance',
    'empty_file',
    'equal_shape_distance_diff_coordinates',
    'fare_transfer_rule_duration_limit_type_without_duration_limit',
    'fare_transfer_rule_duration_limit_without_type',
    'fare_transfer_rule_invalid_transfer_count',
    'fare_transfer_rule_missing_transfer_count',
    'fare_transfer_rule_with_forbidden_transfer_count',
    'forbidden_shape_dist_traveled',
    'invalid_currency',
    'invalid_currency_amount',
    'invalid_url',
    'location_with_unexpected_stop_time',
    'missing_trip_edge',
    'new_line_in_value',
    'point_near_origin',
    'point_near_pole',
    'route_both_short_and_long_name_missing',
    'route_networks_specified_in_more_than_one_file',
    'start_and_end_range_equal',
    'start_and_end_range_out_of_order',
    'station_with_parent_station',
    'stop_time_timepoint_without_times',
    'stop_time_with_arrival_before_previous_departure_time',
    'stop_time_with_only_arrival_or_departure_time',
    'stop_without_location',
    'timeframe_only_start_or_end_time_specified',
    'timeframe_overlap',
    'timeframe_start_or_end_time_greater_than_twenty_four_hours',
    'u_r_i_syntax_error'
]

# errors from the validator that related to pathways
PATHWAYS_FATAL_ERROR_CODES = [
    'bidirectional_exit_gate',
    'pathway_dangling_generic_node',
    'pathway_loop',
    'pathway_to_platform_with_boarding_areas',
    'pathway_to_wrong_location_type',
    'pathway_unreachable_location',
    'missing_level_id',
    'location_without_parent_station'
]

# fields in GTFS by file that are related to pathways
PATHWAYS_FIELDS = {
    'trips.txt': ['wheelchair_accessible'],
    'stops.txt': ['wheelchair_boarding', 'tts_stop_name']
}

# files related to pathways    
PATHWAYS_FILES = ['pathways.txt', 'levels.txt']
