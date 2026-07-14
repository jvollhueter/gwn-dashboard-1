"""Unit tests for temporal aggregation, mapping, and filtering."""

import pandas as pd

from gwn_dashboard.services.aggregation_service import AggregationService


def test_monthly_values_are_summed_separately_by_id_and_year() -> None:
    monthly = pd.DataFrame(
        {
            "id": [1, 1, 1, 2, 2],
            "year": [2000, 2000, 2001, 2000, 2001],
            "month": [1, 2, 1, 1, 1],
            "value": [10.0, 20.0, 50.0, 7.0, 9.0],
        }
    )

    result = AggregationService().monthly_to_yearly_sum(
        monthly,
        "annual_value",
    )

    expected = pd.DataFrame(
        {
            "id": [1, 1, 2, 2],
            "year": [2000, 2001, 2000, 2001],
            "annual_value": [30.0, 50.0, 7.0, 9.0],
        }
    )

    pd.testing.assert_frame_equal(
        result.reset_index(drop=True),
        expected,
    )


def test_groundwater_recharge_combines_matching_rg1_and_rg2_values() -> None:
    rg1 = pd.DataFrame(
        {
            "id": [1, 1, 2],
            "year": [2000, 2001, 2000],
            "month": [1, 1, 1],
            "value": [100.0, 200.0, 300.0],
        }
    )
    rg2 = pd.DataFrame(
        {
            "id": [1, 1, 2],
            "year": [2000, 2001, 2000],
            "month": [1, 1, 1],
            "value": [10.0, 20.0, 30.0],
        }
    )

    result = AggregationService().calculate_groundwater_recharge(
        rg1,
        rg2,
    )

    expected = pd.DataFrame(
        {
            "id": [1, 1, 2],
            "year": [2000, 2001, 2000],
            "gwn": [110.0, 220.0, 330.0],
        }
    )

    pd.testing.assert_frame_equal(
        result.reset_index(drop=True),
        expected,
    )


def test_mapping_attaches_groundwater_body_id() -> None:
    data = pd.DataFrame(
        {
            "id": [1, 2],
            "year": [2000, 2000],
            "value": [100.0, 200.0],
        }
    )
    mapping = pd.DataFrame(
        {
            "id": [1, 2],
            "GWK_ID": ["GWK_A", "GWK_B"],
        }
    )

    result = AggregationService().attach_groundwater_body_id(
        data,
        mapping,
    )

    assert result["GWK_ID"].tolist() == ["GWK_A", "GWK_B"]


def test_filter_keeps_only_selected_groundwater_bodies() -> None:
    data = pd.DataFrame(
        {
            "GWK_ID": ["GWK_A", "GWK_B", "GWK_C"],
            "year": [2000, 2000, 2000],
            "value": [100.0, 200.0, 300.0],
        }
    )

    result = AggregationService().filter_groundwater_bodies(
        data,
        ("GWK_A", "GWK_C"),
    )

    assert result["GWK_ID"].tolist() == ["GWK_A", "GWK_C"]
