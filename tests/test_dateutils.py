"""Test the EyeOnSaur dateutils module."""

from custom_components.eyeonsaur.helpers.dateutils import (
    find_missing_dates,
    sync_reduce_missing_dates,
)
from custom_components.eyeonsaur.models import (
    MissingDate,
    MissingDates,
    StrDate,
    TheoreticalConsumptionData,
    TheoreticalConsumptionDatas,
)


def test_find_missing_dates_empty() -> None:
    """Test with an empty list."""
    assert find_missing_dates(TheoreticalConsumptionDatas([])) == []


def test_find_missing_dates_one_element() -> None:
    """Test with a single element list."""
    data: TheoreticalConsumptionDatas = TheoreticalConsumptionDatas(
        [TheoreticalConsumptionData(StrDate("2024-01-01 00:00:00"), 10.0)]
    )
    assert find_missing_dates(data) == []


def test_find_missing_dates_no_missing() -> None:
    """Test with a list where no dates are missing."""
    data: TheoreticalConsumptionDatas = TheoreticalConsumptionDatas(
        [
            TheoreticalConsumptionData(StrDate("2024-01-01 00:00:00"), 10.0),
            TheoreticalConsumptionData(StrDate("2024-01-02 00:00:00"), 11.0),
            TheoreticalConsumptionData(StrDate("2024-01-03 00:00:00"), 12.0),
        ]
    )

    expected_result: MissingDates = MissingDates([])
    assert find_missing_dates(data) == expected_result


def test_find_missing_dates_with_missing() -> None:
    """Test with a list where dates are missing."""
    data: TheoreticalConsumptionDatas = TheoreticalConsumptionDatas(
        [
            TheoreticalConsumptionData(StrDate("2024-01-01 00:00:00"), 10.0),
            TheoreticalConsumptionData(StrDate("2024-01-03 00:00:00"), 12.0),
            TheoreticalConsumptionData(StrDate("2024-01-05 00:00:00"), 14.0),
        ]
    )

    expected_result: MissingDates = MissingDates(
        [MissingDate(2024, 1, 2), MissingDate(2024, 1, 4)]
    )
    assert find_missing_dates(data) == expected_result


def test_find_missing_dates_unordered() -> None:
    """Test with an unordered list."""
    data: TheoreticalConsumptionDatas = TheoreticalConsumptionDatas(
        [
            TheoreticalConsumptionData(StrDate("2024-01-05 00:00:00"), 14.0),
            TheoreticalConsumptionData(StrDate("2024-01-01 00:00:00"), 10.0),
            TheoreticalConsumptionData(StrDate("2024-01-03 00:00:00"), 12.0),
        ]
    )
    expected_result: MissingDates = MissingDates(
        [MissingDate(2024, 1, 2), MissingDate(2024, 1, 4)]
    )
    assert find_missing_dates(data) == expected_result


def test_find_missing_dates_multiple_missing_same_month() -> None:
    """Test with multiple missing dates in the same month."""
    data: TheoreticalConsumptionDatas = TheoreticalConsumptionDatas(
        [
            TheoreticalConsumptionData(StrDate("2024-01-01 00:00:00"), 10.0),
            TheoreticalConsumptionData(StrDate("2024-01-07 00:00:00"), 15.0),
        ]
    )
    expected_result: MissingDates = MissingDates(
        [
            MissingDate(2024, 1, 2),
            MissingDate(2024, 1, 3),
            MissingDate(2024, 1, 4),
            MissingDate(2024, 1, 5),
            MissingDate(2024, 1, 6),
        ]
    )
    assert find_missing_dates(data) == expected_result


def test_find_missing_dates_multiple_missing_different_months() -> None:
    """Test with multiple missing dates in different months."""
    data: TheoreticalConsumptionDatas = TheoreticalConsumptionDatas(
        [
            TheoreticalConsumptionData(StrDate("2024-01-30 00:00:00"), 10.0),
            TheoreticalConsumptionData(StrDate("2024-02-03 00:00:00"), 15.0),
        ]
    )
    expected_result: MissingDates = MissingDates(
        [
            MissingDate(2024, 1, 31),
            MissingDate(2024, 2, 1),
            MissingDate(2024, 2, 2),
        ]
    )
    assert find_missing_dates(data) == expected_result


def test_sync_reduce_missing_dates_empty() -> None:
    """Test with an empty list."""
    assert sync_reduce_missing_dates(MissingDates([]), set()) == []


def test_sync_reduce_missing_dates_one_element() -> None:
    """Test with a single element list."""
    data: MissingDates = MissingDates([MissingDate(2024, 1, 2)])
    assert sync_reduce_missing_dates(data, set()) == data


def test_sync_reduce_missing_dates_less_than_6_days() -> None:
    """Test with dates less than 6 days apart."""
    data: MissingDates = MissingDates(
        [
            MissingDate(2024, 1, 2),
            MissingDate(2024, 1, 3),
            MissingDate(2024, 1, 8),
        ]
    )
    assert sync_reduce_missing_dates(data, set()) == MissingDates(
        [MissingDate(2024, 1, 2)]
    )


def test_sync_reduce_missing_dates_more_than_6_days() -> None:
    """Test with dates more than 6 days apart."""
    data: MissingDates = MissingDates(
        [
            MissingDate(2024, 1, 2),
            MissingDate(2024, 1, 9),
            MissingDate(2024, 1, 16),
        ]
    )
    assert sync_reduce_missing_dates(data, set()) == MissingDates(
        [
            MissingDate(2024, 1, 2),
            MissingDate(2024, 1, 9),
            MissingDate(2024, 1, 16),
        ]
    )


def test_sync_reduce_missing_dates_with_duplicates() -> None:
    """Test with duplicate dates."""
    data: MissingDates = MissingDates(
        [
            MissingDate(2024, 1, 2),
            MissingDate(2024, 1, 9),
            MissingDate(2024, 1, 9),
            MissingDate(2024, 1, 16),
        ]
    )
    assert sync_reduce_missing_dates(data, set()) == MissingDates(
        [
            MissingDate(2024, 1, 2),
            MissingDate(2024, 1, 9),
            MissingDate(2024, 1, 16),
        ]
    )


def test_sync_reduce_missing_dates_unsorted() -> None:
    """Test with an unsorted list."""
    data: MissingDates = MissingDates(
        [
            MissingDate(2024, 1, 16),
            MissingDate(2024, 1, 2),
            MissingDate(2024, 1, 9),
        ]
    )
    assert sync_reduce_missing_dates(data, set()) == MissingDates(
        [
            MissingDate(2024, 1, 2),
            MissingDate(2024, 1, 9),
            MissingDate(2024, 1, 16),
        ]
    )


def test_sync_reduce_missing_dates_multiple_periods() -> None:
    """Test with multiple periods of missing dates."""
    data: MissingDates = MissingDates(
        [
            MissingDate(2024, 1, 2),
            MissingDate(2024, 1, 9),
            MissingDate(2024, 1, 20),
            MissingDate(2024, 1, 28),
            MissingDate(2024, 2, 5),
        ]
    )
    assert sync_reduce_missing_dates(data, set()) == MissingDates(
        [
            MissingDate(2024, 1, 2),
            MissingDate(2024, 1, 9),
            MissingDate(2024, 1, 20),
            MissingDate(2024, 1, 28),
            MissingDate(2024, 2, 5),
        ]
    )
