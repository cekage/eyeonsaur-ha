"""Test the EyeOnSaur dateutils module."""

from custom_components.eyeonsaur.helpers.dateutils import (
    find_missing_dates,
    sync_reduce_missing_dates,
)


def test_find_missing_dates_empty():
    """Test with an empty list."""
    assert find_missing_dates([]) == []


def test_find_missing_dates_one_element():
    """Test with a single element list."""
    data = [("2024-01-01 00:00:00", 10.0)]
    assert find_missing_dates(data) == []


def test_find_missing_dates_no_missing():
    """Test with a list where no dates are missing."""
    data = [
        ("2024-01-01 00:00:00", 10.0),
        ("2024-01-02 00:00:00", 11.0),
        ("2024-01-03 00:00:00", 12.0),
    ]

    expected_result = []
    assert find_missing_dates(data) == expected_result


def test_find_missing_dates_with_missing():
    """Test with a list where dates are missing."""
    data = [
        ("2024-01-01 00:00:00", 10.0),
        ("2024-01-03 00:00:00", 12.0),
        ("2024-01-05 00:00:00", 14.0),
    ]

    expected_result = [(2024, 1, 2), (2024, 1, 4)]
    assert find_missing_dates(data) == expected_result


def test_find_missing_dates_unordered():
    """Test with an unordered list."""
    data = [
        ("2024-01-05 00:00:00", 14.0),
        ("2024-01-01 00:00:00", 10.0),
        ("2024-01-03 00:00:00", 12.0),
    ]
    expected_result = [(2024, 1, 2), (2024, 1, 4)]
    assert find_missing_dates(data) == expected_result


def test_find_missing_dates_multiple_missing_same_month():
    """Test with multiple missing dates in the same month."""
    data = [
        ("2024-01-01 00:00:00", 10.0),
        ("2024-01-07 00:00:00", 15.0),
    ]
    expected_result = [
        (2024, 1, 2),
        (2024, 1, 3),
        (2024, 1, 4),
        (2024, 1, 5),
        (2024, 1, 6),
    ]
    assert find_missing_dates(data) == expected_result


def test_find_missing_dates_multiple_missing_different_months():
    """Test with multiple missing dates in different months."""
    data = [
        ("2024-01-30 00:00:00", 10.0),
        ("2024-02-03 00:00:00", 15.0),
    ]
    expected_result = [
        (2024, 1, 31),
        (2024, 2, 1),
        (2024, 2, 2),
    ]
    assert find_missing_dates(data) == expected_result


def test_sync_reduce_missing_dates_empty():
    """Test with an empty list."""
    assert sync_reduce_missing_dates([]) == []


def test_sync_reduce_missing_dates_one_element():
    """Test with a single element list."""
    data = [(2024, 1, 2)]
    assert sync_reduce_missing_dates(data) == data


def test_sync_reduce_missing_dates_less_than_6_days():
    """Test with dates less than 6 days apart."""
    data = [(2024, 1, 2), (2024, 1, 3), (2024, 1, 8)]
    assert sync_reduce_missing_dates(data) == [(2024, 1, 2)]


def test_sync_reduce_missing_dates_more_than_6_days():
    """Test with dates more than 6 days apart."""
    data = [(2024, 1, 2), (2024, 1, 9), (2024, 1, 16)]
    assert sync_reduce_missing_dates(data) == [
        (2024, 1, 2),
        (2024, 1, 9),
        (2024, 1, 16),
    ]


def test_sync_reduce_missing_dates_with_duplicates():
    """Test with duplicate dates."""
    data = [(2024, 1, 2), (2024, 1, 9), (2024, 1, 9), (2024, 1, 16)]
    assert sync_reduce_missing_dates(data) == [
        (2024, 1, 2),
        (2024, 1, 9),
        (2024, 1, 16),
    ]


def test_sync_reduce_missing_dates_unsorted():
    """Test with an unsorted list."""
    data = [(2024, 1, 16), (2024, 1, 2), (2024, 1, 9)]
    assert sync_reduce_missing_dates(data) == [
        (2024, 1, 2),
        (2024, 1, 9),
        (2024, 1, 16),
    ]


def test_sync_reduce_missing_dates_multiple_periods():
    """Test with multiple periods of missing dates."""
    data = [
        (2024, 1, 2),
        (2024, 1, 9),
        (2024, 1, 20),
        (2024, 1, 28),
        (2024, 2, 5),
    ]
    assert sync_reduce_missing_dates(data) == [
        (2024, 1, 2),
        (2024, 1, 9),
        (2024, 1, 20),
        (2024, 1, 28),
        (2024, 2, 5),
    ]
