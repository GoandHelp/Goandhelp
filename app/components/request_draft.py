import reflex as rx

from app.interface_i18n import ui
from app.components.map_picker import map_picker
from app.countries import CURRENCY_OPTIONS
from app.skill_categories import CATEGORY_CHOICES
from app.states.help_hub_state import REWARD_CHOICES
from app.states.onboarding_state import OnboardingState

INPUT = "w-full rounded-xl border border-[#f6c66f] bg-white px-3 py-2 text-sm text-[#292929] focus-visible:outline-2 focus-visible:outline-[#e08b12]"
SELECT = "w-full appearance-none rounded-xl border border-[#f6c66f] bg-white px-3 py-2 pr-9 text-sm text-[#292929] focus-visible:outline-2 focus-visible:outline-[#e08b12]"


def draft_input(
    label: str, value: rx.Var[str], change: rx.event.EventType, **props
) -> rx.Component:
    return rx.el.label(
        rx.el.span(
            ui(label), class_name="text-sm font-semibold text-[#404040]"
        ),
        rx.el.input(
            default_value=value, on_change=change, class_name=INPUT, **props
        ),
        class_name="flex w-full flex-col gap-1.5 text-left",
    )


def draft_select(
    label: str,
    choices: list[dict[str, str]],
    value: rx.Var[str],
    change: rx.event.EventType,
    onboarding_rewards: bool = False,
) -> rx.Component:
    return rx.el.label(
        rx.el.span(
            rx.el.span(
                ui(label), class_name="text-sm font-semibold text-[#404040]"
            ),
            rx.cond(
                onboarding_rewards,
                rx.el.span(
                    ui("optional — defaults to Free"),
                    class_name="text-right text-xs font-normal text-[#525252]",
                ),
                rx.fragment(),
            ),
            class_name="flex w-full items-center justify-between gap-2",
        ),
        rx.el.div(
            rx.el.select(
                rx.el.option(ui("Choose…"), value="", disabled=True),
                rx.foreach(
                    choices,
                    lambda item: rx.el.option(
                        rx.cond(
                            onboarding_rewards,
                            f"{ui(item['label'])} – {ui(item.get('blurb', ''))}",
                            ui(item["label"]),
                        ),
                        value=item["value"],
                    ),
                ),
                value=value,
                on_change=change,
                class_name=SELECT,
            ),
            rx.icon(
                "chevron-down",
                class_name="pointer-events-none absolute right-3 top-1/2 size-4 -translate-y-1/2 text-[#e08b12]",
            ),
            class_name="relative w-full",
        ),
        class_name="flex w-full flex-col gap-1.5 text-left",
    )


def onboarding_reward_row(item: dict[str, str]) -> rx.Component:
    return rx.el.button(
        rx.icon(
            "check",
            class_name=rx.cond(
                OnboardingState.request_rewards.contains(item["value"]),
                "size-5 shrink-0 rounded border border-[#e08b12] bg-[#e08b12] text-white",
                "size-5 shrink-0 rounded border border-[#e08b12] bg-white text-transparent",
            ),
        ),
        rx.el.span(
            rx.el.strong(ui(item["label"]), class_name="font-bold"),
            rx.el.span(f" – {ui(item['blurb'])}", class_name="font-normal"),
        ),
        type="button",
        role="checkbox",
        aria_checked=OnboardingState.request_rewards.contains(item["value"]),
        disabled=OnboardingState.saving,
        on_click=lambda: OnboardingState.toggle_request_reward(item["value"]),
        class_name=rx.cond(
            OnboardingState.request_rewards.contains(item["value"]),
            "flex w-full items-center gap-3 bg-[#fff7e8] p-3 text-left text-sm text-[#292929]",
            "flex w-full items-center gap-3 bg-white p-3 text-left text-sm text-[#292929] hover:bg-[#fff7e8]",
        ),
    )


def onboarding_reward_detail(item: dict[str, str]) -> rx.Component:
    return rx.cond(
        OnboardingState.request_rewards.contains(item["value"])
        & (item["value"] != "money"),
        draft_input(
            item["label"],
            OnboardingState.request_reward_specs.get(item["value"], ""),
            lambda value: OnboardingState.set_request_reward_spec(
                item["value"], value
            ),
            min_length=3,
            max_length=120,
            required=True,
        ),
        rx.fragment(),
    )


def onboarding_rewards() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.p(
                ui("Rewards"), class_name="text-sm font-semibold text-[#404040]"
            ),
            rx.el.p(
                ui("optional — defaults to Free"),
                class_name="text-right text-xs text-[#525252]",
            ),
            class_name="flex w-full items-center justify-between gap-2",
        ),
        rx.el.div(
            rx.foreach(REWARD_CHOICES, onboarding_reward_row),
            role="group",
            aria_label=ui("Rewards — select any number"),
            class_name="w-full overflow-hidden rounded-xl border border-[#f6c66f] divide-y divide-[#f6c66f] bg-white",
        ),
        rx.cond(
            OnboardingState.request_rewards.length() > 0,
            rx.el.p(
                ui("Please specify for each one below"),
                class_name="text-sm font-semibold text-[#404040]",
            ),
            rx.fragment(),
        ),
        rx.foreach(REWARD_CHOICES, onboarding_reward_detail),
        class_name="flex w-full flex-col gap-3 text-left",
    )


def compact_request_fields(
    state, picker_key: str, show_date: bool = True
) -> rx.Component:
    return rx.el.div(
        draft_input(
            "Job Title",
            state.request_title,
            lambda value: state.set_request_field.debounce(500)(
                "request_title", value
            ),
            min_length=4,
            max_length=160,
        ),
        rx.el.label(
            rx.el.span(
                ui("Job description"),
                class_name="text-sm font-semibold text-[#404040]",
            ),
            rx.el.textarea(
                default_value=state.request_description,
                on_change=lambda value: state.set_request_field.debounce(500)(
                    "request_description", value
                ),
                rows="4",
                min_length=15,
                max_length=500,
                class_name=INPUT,
            ),
            class_name="flex w-full flex-col gap-1.5 text-left",
        ),
        rx.el.div(
            draft_select(
                "Job category",
                CATEGORY_CHOICES,
                state.request_category,
                lambda value: state.set_request_field.debounce(500)(
                    "request_category", value
                ),
            ),
            rx.cond(
                show_date,
                draft_input(
                    "Date",
                    state.request_date,
                    lambda value: state.set_request_field.debounce(500)(
                        "request_date", value
                    ),
                    type="date",
                    min=state.request_date_min,
                    max=state.request_date_max,
                ),
                rx.fragment(),
            ),
            class_name=rx.cond(
                show_date,
                "grid w-full grid-cols-1 gap-4 sm:grid-cols-2",
                "w-full text-left",
            ),
        ),
        rx.el.div(
            rx.el.p(
                ui("Location of this request"),
                class_name="text-center text-sm font-semibold text-[#404040]",
            ),
            rx.el.p(
                ui(
                    "Your exact pin stays private. Helpers see an approximate area until confirmed."
                ),
                class_name="mt-1 text-center text-xs text-[#525252]",
            ),
            map_picker(picker_key, "Location of this request", inline=True),
            class_name="w-full px-5 text-left sm:px-6",
        ),
        rx.cond(
            picker_key == "onboarding-first-request",
            onboarding_rewards(),
            draft_select(
                "Rewards",
                REWARD_CHOICES,
                state.request_reward,
                lambda value: state.set_request_field.debounce(500)(
                    "request_reward", value
                ),
            ),
        ),
        rx.cond(
            rx.cond(
                picker_key == "onboarding-first-request",
                OnboardingState.request_rewards.contains("money"),
                state.request_reward == "money",
            ),
            rx.el.div(
                draft_select(
                    "Currency",
                    CURRENCY_OPTIONS,
                    state.request_currency,
                    lambda value: state.set_request_field.debounce(500)(
                        "request_currency", value
                    ),
                ),
                rx.cond(
                    ~state.request_quote,
                    draft_input(
                        "Enter your budget",
                        state.request_budget,
                        lambda value: state.set_request_field.debounce(500)(
                            "request_budget", value
                        ),
                        type="text",
                        input_mode="decimal",
                        pattern=r"[0-9]{1,8}(\.[0-9]{1,2})?",
                        auto_complete="off",
                        max_length=11,
                    ),
                    rx.fragment(),
                ),
                rx.el.button(
                    rx.icon(
                        "check",
                        class_name=rx.cond(
                            state.request_quote,
                            "size-4 text-[#e08b12]",
                            "size-4 text-gray-300",
                        ),
                    ),
                    ui("Ask helper for an estimate price"),
                    type="button",
                    role="checkbox",
                    aria_checked=state.request_quote,
                    on_click=state.toggle_request_quote,
                    class_name="flex items-center justify-center gap-2 rounded-xl border border-[#f6c66f] bg-white px-3 py-2 text-sm text-[#404040]",
                ),
                rx.el.p(
                    ui("Go and Help receives an 8% fee"),
                    class_name="text-center text-sm font-medium text-[#e08b12]",
                ),
                class_name="flex w-full flex-col gap-3 rounded-xl bg-[#fff7e8] p-3",
            ),
            rx.fragment(),
        ),
        rx.cond(
            (picker_key != "onboarding-first-request")
            & (state.request_reward == "other_reward"),
            draft_input(
                "Other reward details",
                state.request_other,
                lambda value: state.set_request_field.debounce(500)(
                    "request_other", value
                ),
                min_length=3,
                max_length=500,
            ),
            rx.fragment(),
        ),
        class_name="flex w-full flex-col gap-4 bg-transparent text-[#292929]",
    )
