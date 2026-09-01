from backend.app.models.recipe import Recipe
from backend.app.services.recipe_loader import (
    parse_time_minutes,
)


def test_zero_time_becomes_none():
    assert parse_time_minutes(0) is None


def test_positive_time_is_preserved():
    assert parse_time_minutes(25) == 25