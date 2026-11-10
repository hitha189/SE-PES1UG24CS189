import pytest
from car_rental_rate import process_rental_fleet, check_fleet_telematics


def rental(**kw):
    base = {"is_confirmed": True, "vehicle_type": "economy",
            "driver_age": 30, "days": 1, "trip_segments": []}
    base.update(kw)
    return base


# ---------- process_rental_fleet : input validation (both operands of 'or') ----------
def test_non_list_input_raises():
    with pytest.raises(ValueError):
        process_rental_fleet("not a list", 10.0)


def test_negative_admin_fee_raises():
    with pytest.raises(ValueError):
        process_rental_fleet([rental()], -1.0)


def test_zero_admin_fee_is_valid():
    assert process_rental_fleet([rental()], 0.0)["total_revenue"] == 40.0


# ---------- loop never entered / defaults ----------
def test_empty_list_is_empty_batch():
    assert process_rental_fleet([], 10.0) == {"total_revenue": 0.0, "status": "EMPTY_BATCH"}


def test_missing_keys_use_defaults():
    # confirmed, defaults: economy, age 25, 1 day, no segments -> 40 + fee
    result = process_rental_fleet([{"is_confirmed": True}], 5.0)
    assert result == {"total_revenue": 45.0, "status": "STANDARD"}


def test_unconfirmed_rental_is_skipped():
    result = process_rental_fleet([rental(is_confirmed=False)], 10.0)
    assert result["status"] == "EMPTY_BATCH"


def test_missing_is_confirmed_key_is_skipped():
    assert process_rental_fleet([{"days": 3}], 10.0)["status"] == "EMPTY_BATCH"


# ---------- days check ----------
def test_zero_days_is_risk_and_skipped():
    assert process_rental_fleet([rental(days=0)], 10.0)["status"] == "EMPTY_BATCH"


def test_negative_days_is_skipped():
    assert process_rental_fleet([rental(days=-2)], 10.0)["status"] == "EMPTY_BATCH"


def test_one_day_boundary_is_valid():
    assert process_rental_fleet([rental(days=1)], 0.0)["total_revenue"] == 40.0


# ---------- vehicle type ----------
def test_luxury_rate():
    assert process_rental_fleet([rental(vehicle_type="luxury", days=2)], 0.0)["total_revenue"] == 240.0


def test_suv_rate():
    assert process_rental_fleet([rental(vehicle_type="suv", days=2)], 0.0)["total_revenue"] == 140.0


def test_economy_rate():
    assert process_rental_fleet([rental(vehicle_type="economy", days=2)], 0.0)["total_revenue"] == 80.0


def test_unknown_vehicle_type_falls_to_economy_rate():
    assert process_rental_fleet([rental(vehicle_type="van", days=2)], 0.0)["total_revenue"] == 80.0


# ---------- trip segments ----------
def test_no_segments():
    assert process_rental_fleet([rental(trip_segments=[])], 0.0)["total_revenue"] == 40.0


def test_negative_miles_flagged_and_ignored():
    result = process_rental_fleet([rental(trip_segments=[-5, 100])], 0.0)
    assert result["total_revenue"] == pytest.approx(40.0 + 100 * 0.20)


def test_miles_exactly_300_uses_normal_rate():
    result = process_rental_fleet([rental(trip_segments=[300])], 0.0)
    assert result["total_revenue"] == pytest.approx(40.0 + 300 * 0.20)


def test_miles_301_uses_long_trip_rate_for_adult():
    result = process_rental_fleet([rental(trip_segments=[301])], 0.0)
    assert result["total_revenue"] == pytest.approx(40.0 + 301 * 0.40)


def test_long_trip_driver_exactly_21_pays_per_mile():
    result = process_rental_fleet([rental(driver_age=21, trip_segments=[400])], 0.0)
    # 21 is not < 21 -> per-mile; but 21 < 25 -> +20 young driver fee
    assert result["total_revenue"] == pytest.approx(40.0 + 400 * 0.40 + 20.0)


def test_long_trip_driver_20_flat_fee_and_break():
    result = process_rental_fleet(
        [rental(driver_age=20, trip_segments=[400, 100])], 0.0)
    # break skips the 100-mile segment
    assert result["total_revenue"] == pytest.approx(40.0 + 250.0 + 20.0)


# ---------- young driver surcharge ----------
def test_age_25_no_surcharge():
    assert process_rental_fleet([rental(driver_age=25, days=2)], 0.0)["total_revenue"] == 80.0


def test_age_24_non_luxury_surcharge():
    assert process_rental_fleet([rental(driver_age=24, days=2)], 0.0)["total_revenue"] == 80.0 + 40.0


def test_age_24_luxury_surcharge():
    result = process_rental_fleet(
        [rental(driver_age=24, vehicle_type="luxury", days=2)], 0.0)
    assert result["total_revenue"] == 240.0 + 100.0


# ---------- final status ----------
def test_risk_flags_exactly_4_is_not_audit():
    rentals = [rental(days=0) for _ in range(4)] + [rental()]
    assert process_rental_fleet(rentals, 0.0)["status"] == "STANDARD"


def test_risk_flags_5_is_high_risk_audit():
    rentals = [rental(days=0) for _ in range(5)] + [rental()]
    result = process_rental_fleet(rentals, 0.0)
    assert result == {"total_revenue": 40.0, "status": "HIGH_RISK_AUDIT"}


def test_zero_total_revenue_is_empty_batch():
    assert process_rental_fleet([rental(is_confirmed=False)], 0.0)["status"] == "EMPTY_BATCH"


def test_single_economy_rental_standard():
    result = process_rental_fleet([rental(days=2, trip_segments=[100])], 10.0)
    assert result == {"total_revenue": 110.0, "status": "STANDARD"}


# ---------- check_fleet_telematics ----------
def test_telematics_none_is_no_data():
    assert check_fleet_telematics(None) == "NO_DATA"


def test_telematics_empty_matrix_is_no_data():
    assert check_fleet_telematics([]) == "NO_DATA"


def test_telematics_two_consecutive_speeding_grounds_vehicle():
    assert check_fleet_telematics([[80, 105, 110]]) == "GROUND_VEHICLE"


def test_telematics_streak_resets_when_slowing():
    assert check_fleet_telematics([[101, 90, 101, 80]]) == "SAFE"


def test_telematics_exactly_100_is_not_speeding():
    assert check_fleet_telematics([[100, 100, 100]]) == "SAFE"


def test_telematics_vehicle_with_no_logs():
    assert check_fleet_telematics([[]]) == "SAFE"


def test_telematics_streak_does_not_carry_across_vehicles():
    assert check_fleet_telematics([[120], [120]]) == "SAFE"


def test_telematics_second_vehicle_grounded():
    assert check_fleet_telematics([[50, 60], [110, 120]]) == "GROUND_VEHICLE"
