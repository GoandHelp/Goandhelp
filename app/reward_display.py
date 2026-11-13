import reflex as rx

from decimal import Decimal, ROUND_HALF_UP

from app.countries import supported_currency

REWARD_LABELS: dict[str, str] = {
    "lunch": "Lunch",
    "dinner": "Dinner",
    "accommodation": "Accommodation",
    "guided_tours": "Guided tours",
    "workshops": "Workshops",
    "lessons": "Lessons",
    "other": "Other",
    "meal": "Meal",
    "gratitude_only": "Free",
}


def reward_display(
    reward: str,
    reward_types: str,
    value: Decimal | int | float,
    currency: str,
    details: str,
) -> str:
    kinds = {
        part.strip().lower() for part in (reward_types or reward).split(",")
    }
    if "money" in kinds:
        code = supported_currency(currency or "USD")
        amount = Decimal(value or 0)
        if amount > 0:
            rounded = amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            return f"Reward: {rounded:.0f}{code}"
        if "helper quote requested" in details.lower():
            return f"Reward: Quote requested ({code})"
    if reward in ("other", "other_reward") and details.strip():
        return f"Reward: {details.strip()}"
    return (
        f"Reward: {REWARD_LABELS.get(reward, reward.replace('_', ' ').title())}"
    )
