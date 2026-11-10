import pytest
from car_rental_rate import process_rental_fleet, check_fleet_telematics


def rental(**kw):
    base = {"is_confirmed": True, "vehicle_type": "economy",
            "driver_age": 30, "days": 1, "trip_segments": []}
    base.update(kw)
    return base


# ---------- process_rental_fleet ----------
def test_single_economy_rental():
    result = process_rental_fleet([rental(days=2, trip_segments=[100])], 10.0)
    assert result == {"total_revenue": 110.0, "status": "STANDARD"}


def test_invalid_input_raises():
    with pytest.raises(ValueError):
        process_rental_fleet("not a list", 10.0)


def test_unconfirmed_rental_is_skipped():
    result = process_rental_fleet([rental(is_confirmed=False)], 10.0)
    assert result["status"] == "EMPTY_BATCH"


def test_zero_days_is_risk_and_skipped():
    result = process_rental_fleet([rental(days=0)], 10.0)
    assert result == {"total_revenue": 0.0, "status": "EMPTY_BATCH"}


def test_luxury_rate():
    result = process_rental_fleet([rental(vehicle_type="luxury", days=2)], 0.0)
    assert result["total_revenue"] == 240.0


def test_suv_rate():
    result = process_rental_fleet([rental(vehicle_type="suv", days=2)], 0.0)
    assert result["total_revenue"] == 140.0


def test_negative_miles_flagged_and_ignored():
    result = process_rental_fleet([rental(trip_segments=[-5, 100])], 0.0)
    assert result["total_revenue"] == 40.0 + 100 * 0.20


def test_long_trip_adult_surcharge():
    result = process_rental_fleet([rental(trip_segments=[400])], 0.0)
    assert result["total_revenue"] == 40.0 + 400 * 0.40


def test_long_trip_underage_flat_fee_and_break():
    # age 20 -> +250 flat, break (second segment ignored), + 20*1 young-driver fee
    result = process_rental_fleet(
        [rental(driver_age=20, trip_segments=[400, 100])], 0.0)
    assert result["total_revenue"] == 40.0 + 250.0 + 20.0


def test_young_driver_luxury_fee():
    result = process_rental_fleet(
        [rental(driver_age=22, vehicle_type="luxury", days=2)], 0.0)
    assert result["total_revenue"] == 240.0 + 100.0


def test_young_driver_non_luxury_fee():
    result = process_rental_fleet([rental(driver_age=22, days=2)], 0.0)
    assert result["total_revenue"] == 80.0 + 40.0


def test_high_risk_audit():
    rentals = [rental(days=0) for _ in range(5)]
    result = process_rental_fleet(rentals, 0.0)
    assert result["status"] == "HIGH_RISK_AUDIT"


# ---------- check_fleet_telematics ----------
def test_telematics_no_data():
    assert check_fleet_telematics([]) == "NO_DATA"


def test_telematics_ground_vehicle():
    assert check_fleet_telematics([[80, 105, 110]]) == "GROUND_VEHICLE"


def test_telematics_safe_with_streak_reset():
    assert check_fleet_telematics([[101, 90, 101, 80]]) == "SAFE"
