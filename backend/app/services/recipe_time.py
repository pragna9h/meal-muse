from backend.app.models.recipe import Recipe


def get_effective_total_time(
    recipe: Recipe,
) -> int | None:
    prep_time = recipe.prep_time_minutes
    cook_time = recipe.cook_time_minutes

    valid_prep = (
        prep_time
        if prep_time is not None and prep_time > 0
        else None
    )

    valid_cook = (
        cook_time
        if cook_time is not None and cook_time > 0
        else None
    )

    if valid_prep is not None or valid_cook is not None:
        return (
            (valid_prep or 0)
            + (valid_cook or 0)
        )

    if (
        recipe.total_time_minutes is not None
        and recipe.total_time_minutes > 0
    ):
        return recipe.total_time_minutes

    return None