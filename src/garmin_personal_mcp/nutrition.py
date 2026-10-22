import datetime

from .garmin_api import query


def get_food_log(
    client,
    day: datetime.date,
    *,
    meal_id: int | None = None,
    include_goals: bool = True,
    include_nutrition: bool = True,
    include_media: bool = False,
) -> dict | None:
    return client.get(
        f"/nutrition-service/food/logs/{day}",
        params=query(
            mealId=meal_id,
            includeGoals=include_goals,
            includeNutrition=include_nutrition,
            includeMedia=include_media,
        ),
    )
