from datetime import datetime
from decimal import Decimal
import pytest

from backend.src.models.risk_parameters import RiskParameters


def test_valid_risk_parameters_pass():
    params = RiskParameters(
        user_id="user-123",
        max_bet_size=Decimal("100.00"),
        max_daily_bets=10,
        max_parallel_positions=3,
        min_probability_edge=Decimal("0.05"),
        frequency_limit_minutes=15,
        max_daily_loss=Decimal("500.00"),
    )
    assert params.user_id == "user-123"
    assert Decimal(params.min_probability_edge) == Decimal("0.05")
    assert params.created_at <= datetime.utcnow()


@pytest.mark.parametrize("edge", [Decimal("0.0"), Decimal("0.009"), Decimal("0.25")])
def test_min_probability_edge_out_of_range_raises(edge):
    with pytest.raises(ValueError):
        RiskParameters(
            user_id="u",
            max_bet_size=Decimal("100"),
            max_daily_bets=1,
            max_parallel_positions=1,
            min_probability_edge=edge,
            frequency_limit_minutes=1,
            max_daily_loss=Decimal("100"),
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("max_bet_size", Decimal("0")),
        ("max_bet_size", Decimal("-1")),
        ("max_daily_loss", Decimal("0")),
        ("max_daily_loss", Decimal("-10")),
    ],
)
def test_positive_decimal_fields_must_be_positive(field, value):
    kwargs = dict(
        user_id="u",
        max_bet_size=Decimal("100"),
        max_daily_bets=1,
        max_parallel_positions=1,
        min_probability_edge=Decimal("0.05"),
        frequency_limit_minutes=1,
        max_daily_loss=Decimal("100"),
    )
    kwargs[field] = value
    with pytest.raises(ValueError):
        RiskParameters(**kwargs)


@pytest.mark.parametrize(
    "field,value",
    [
        ("max_daily_bets", 0),
        ("max_daily_bets", -1),
        ("max_parallel_positions", 0),
        ("max_parallel_positions", -3),
        ("frequency_limit_minutes", 0),
        ("frequency_limit_minutes", -5),
    ],
)
def test_positive_integer_fields_must_be_positive(field, value):
    kwargs = dict(
        user_id="u",
        max_bet_size=Decimal("100"),
        max_daily_bets=1,
        max_parallel_positions=1,
        min_probability_edge=Decimal("0.05"),
        frequency_limit_minutes=1,
        max_daily_loss=Decimal("100"),
    )
    kwargs[field] = value
    with pytest.raises(ValueError):
        RiskParameters(**kwargs)

