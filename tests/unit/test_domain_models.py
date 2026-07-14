"""Unit tests for the domain models."""

import pytest

from gwn_dashboard.domain.models import Period


def test_period_contains_inclusive_boundaries() -> None:
    period = Period(
        label="1961–1990",
        start_year=1961,
        end_year=1990,
    )

    assert period.contains(1961)
    assert period.contains(1990)
    assert not period.contains(1960)
    assert not period.contains(1991)


def test_period_rejects_start_year_after_end_year() -> None:
    with pytest.raises(
        ValueError,
        match="start_year must not be greater than end_year",
    ):
        Period(
            label="Ungültige Periode",
            start_year=2000,
            end_year=1990,
        )
