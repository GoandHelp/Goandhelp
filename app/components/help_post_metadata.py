import json

import reflex as rx
from reflex.vars.base import VarData

from app.interface_i18n import ui, ui_template
from app.interface_catalog_help_post_metadata import HELP_POST_METADATA_KEYS
from app.reward_display import REWARD_LABELS
from app.models import HELP_DURATION_OPTIONS
from app.states.auth_state import AuthState


def localized_metadata(value: str | rx.Var[str]) -> rx.Var[str]:
    source = rx.Var.create(value)
    fallback = ui(source)
    count = rx.Var(
        _js_expr=f"String({source}).match(/^Every ([0-9]+) (days|weeks|months)$/)?.[1] ?? ''",
        _var_type=str,
        _var_data=source._get_all_var_data(),
    )
    unit = rx.Var(
        _js_expr=f"String({source}).match(/^Every ([0-9]+) (days|weeks|months)$/)?.[2] ?? ''",
        _var_type=str,
        _var_data=source._get_all_var_data(),
    )
    days = ui_template("Every {count} days", "count", count)
    weeks = ui_template("Every {count} weeks", "count", count)
    months = ui_template("Every {count} months", "count", count)
    known_sources = json.dumps(
        list(
            dict.fromkeys(
                (
                    *HELP_POST_METADATA_KEYS,
                    *(option["label"] for option in HELP_DURATION_OPTIONS),
                    *REWARD_LABELS.values(),
                    "Meal",
                    "Free",
                )
            )
        ),
        ensure_ascii=False,
    )
    return rx.Var(
        _js_expr=(
            f"(() => {{ const text = String({source}); "
            f"if ({known_sources}.includes(text)) return {fallback}; "
            f"const unit = {unit}; "
            f"if (unit === 'days') return {days}; "
            f"if (unit === 'weeks') return {weeks}; "
            f"if (unit === 'months') return {months}; "
            f"return text; }})()"
        ),
        _var_type=str,
        _var_data=VarData.merge(
            source._get_all_var_data(),
            fallback._get_all_var_data(),
            days._get_all_var_data(),
            weeks._get_all_var_data(),
            months._get_all_var_data(),
        ),
    ).to(str)


def localized_date_time(
    iso_value: str | rx.Var[str],
    date_only: bool = False,
    fallback_key: str = "Time to agree",
    legacy_value: str | rx.Var[str] = "",
) -> rx.Var[str]:
    source = rx.Var.create(iso_value)
    legacy = rx.Var.create(legacy_value)
    fallback = ui(fallback_key)
    language = AuthState.preferred_language
    if date_only:
        formatted = (
            f"new Intl.DateTimeFormat(String({language} || 'en'), "
            "{calendar: 'gregory', timeZone: 'UTC', year: 'numeric', "
            "month: 'short', day: 'numeric'}).format(new Date(iso))"
        )
    else:
        formatted = (
            f"(() => {{ const date = new Date(iso); "
            f"const locale = String({language} || 'en'); "
            "const options = {calendar: 'gregory', timeZone: 'UTC', "
            "year: 'numeric', month: 'short', day: 'numeric'}; "
            "const timeOptions = {calendar: 'gregory', timeZone: 'UTC', "
            "hour: '2-digit', minute: '2-digit', hourCycle: 'h23'}; "
            "const day = new Intl.DateTimeFormat(locale, options).format(date); "
            "const time = new Intl.DateTimeFormat(locale, timeOptions).format(date); "
            "return `${day} · ${time}`; })()"
        )
    return rx.Var(
        _js_expr=(
            f"(() => {{ const iso = String({source} || ''); "
            f"if (!iso) {{ const legacy = String({legacy} || ''); "
            f"return legacy && legacy !== {json.dumps(fallback_key)} ? legacy : {fallback}; }} "
            f"return {formatted}; }})()"
        ),
        _var_type=str,
        _var_data=VarData.merge(
            source._get_all_var_data(),
            legacy._get_all_var_data(),
            language._get_all_var_data(),
            fallback._get_all_var_data(),
        ),
    ).to(str)


def localized_reward(
    value: str | rx.Var[str], custom_payload: bool | rx.Var[bool] = False
) -> rx.Var[str]:
    source = rx.Var.create(value)
    is_custom = rx.Var.create(custom_payload).to(bool)
    payload = rx.Var(
        _js_expr=f"String({source}).startsWith('Reward: ') ? String({source}).slice(8) : String({source})",
        _var_type=str,
        _var_data=source._get_all_var_data(),
    )
    fallback = ui_template("Reward: {reward}", "reward", payload)
    custom_result = ui_template("Reward: {reward}", "reward", payload)

    known_cases = []
    for label in dict.fromkeys((*REWARD_LABELS.values(), "Meal", "Free")):
        localized = ui_template("Reward: {reward}", "reward", ui(label))
        known_cases.append(
            (
                f"String({source}) === {json.dumps(f'Reward: {label}', ensure_ascii=False)}",
                localized,
            )
        )

    amount = rx.Var(
        _js_expr=f"String({source}).match(/^Reward: ([0-9]+)([A-Z]{{3}})$/)?.[1] ?? ''",
        _var_type=str,
        _var_data=source._get_all_var_data(),
    )
    currency = rx.Var(
        _js_expr=f"String({source}).match(/^Reward: ([0-9]+)([A-Z]{{3}})$/)?.[2] ?? ''",
        _var_type=str,
        _var_data=source._get_all_var_data(),
    )
    money_result = ui_template(
        "Reward: {amount}{currency}",
        "amount",
        amount,
    )
    money_result = rx.Var(
        _js_expr=f"({money_result}).split('{{currency}}').join({currency})",
        _var_type=str,
        _var_data=VarData.merge(
            money_result._get_all_var_data(), currency._get_all_var_data()
        ),
    )
    quote_currency = rx.Var(
        _js_expr=f"String({source}).match(/^Reward: Quote requested \\(([A-Z]{{3}})\\)\\.?$/)?.[1] ?? ''",
        _var_type=str,
        _var_data=source._get_all_var_data(),
    )
    quote_result = ui_template(
        "Reward: Quote requested ({currency}).", "currency", quote_currency
    )
    money_match = f"/^Reward: [0-9]+[A-Z]{{3}}$/.test(String({source}))"
    quote_match = f"/^Reward: Quote requested \\([A-Z]{{3}}\\)\\.?$/.test(String({source}))"
    localized = str(fallback)
    for condition, result in reversed(known_cases):
        localized = f"({condition} ? {result} : {localized})"
    localized = (
        f"({money_match} ? {money_result} : "
        f"({quote_match} ? {quote_result} : {localized}))"
    )
    custom_js = f"({custom_result})"
    expression = (
        f"(() => {{ if ({is_custom}) return {custom_js}; "
        f"return {localized}; }})()"
    )
    return rx.Var(
        _js_expr=expression,
        _var_type=str,
        _var_data=VarData.merge(
            source._get_all_var_data(),
            is_custom._get_all_var_data(),
            fallback._get_all_var_data(),
            custom_result._get_all_var_data(),
            *(result._get_all_var_data() for _condition, result in known_cases),
            money_result._get_all_var_data(),
            quote_result._get_all_var_data(),
        ),
    ).to(str)
