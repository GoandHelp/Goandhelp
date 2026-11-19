import json
import re

import reflex as rx
from reflex.vars.base import VarData

from app.interface_catalog_help_hub_feedback import HELP_HUB_FEEDBACK_KEYS
from app.interface_i18n import ui
from app.states.auth_state import AuthState

_REQUEST_ERRORS: tuple[str, ...] = (
    *HELP_HUB_FEEDBACK_KEYS[:25],
    "Your session expired — please sign in again.",
    "Pick at least one category so helpers know what kind of task this is.",
    "Number of people required must be a whole number from 1 to 500.",
)

_MONEY_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "Enter your budget in {currency} with at most two decimal places, or allow a Helper quote.",
        re.compile(
            r"^Enter your budget in ([A-Z]{3}) with at most two decimal places, or allow a Helper quote\.(?![\s\S])"
        ),
    ),
    (
        "Enter a positive {currency} budget from 0.01 to 99999999.99, or allow a Helper quote.",
        re.compile(
            r"^Enter a positive ([A-Z]{3}) budget from 0\.01 to 99999999\.99, or allow a Helper quote\.(?![\s\S])"
        ),
    ),
)

_MISSING_FIELD_LABELS: tuple[str, ...] = (
    "Job title",
    "Job description",
    "Job category",
    "Date",
    "Address",
    "City",
    "Country",
    "Rewards",
    "Number of nights",
    "Guided tour details",
    "Activity details",
    "Other reward details",
    "Enter your budget",
)

_SUCCESS_PATTERN = re.compile(
    r'^"([\s\S]*)" is live — helpers nearby can offer their hands now\.(?![\s\S])'
)


def _localized_exact(
    value: str | rx.Var[str], sources: tuple[str, ...]
) -> rx.Var[str]:
    source = rx.Var.create(value).to(str)
    localized = [(key, ui(key)) for key in sources]
    translations = ", ".join(
        f"{json.dumps(key, ensure_ascii=False)}: {translation}"
        for key, translation in localized
    )
    expression = (
        f"(() => {{ const text = String({source} ?? ''); "
        f"const translations = {{{translations}}}; "
        "return Object.prototype.hasOwnProperty.call(translations, text) "
        "? translations[text] : text; })()"
    )
    return rx.Var(
        _js_expr=expression,
        _var_type=str,
        _var_data=VarData.merge(
            source._get_all_var_data(),
            *(
                translation._get_all_var_data()
                for _key, translation in localized
            ),
        ),
    ).to(str)


def localized_request_error(value: str | rx.Var[str]) -> rx.Var[str]:
    source = rx.Var.create(value).to(str)
    exact = _localized_exact(source, _REQUEST_ERRORS)
    branches: list[tuple[str, rx.Var[str]]] = []
    for template, pattern in _MONEY_PATTERNS:
        translated = ui(template)
        match = f"String({source} ?? '').match({json.dumps(pattern.pattern)})"
        branches.append(
            (
                match,
                rx.Var(
                    _js_expr=(
                        f"({translated}).split('{{currency}}').join({match}[1])"
                    ),
                    _var_type=str,
                    _var_data=VarData.merge(
                        source._get_all_var_data(),
                        translated._get_all_var_data(),
                    ),
                ).to(str),
            )
        )
    expression = str(exact)
    for match, localized in reversed(branches):
        expression = f"({match} ? {localized} : {expression})"
    return rx.Var(
        _js_expr=expression,
        _var_type=str,
        _var_data=VarData.merge(
            source._get_all_var_data(),
            exact._get_all_var_data(),
            *(localized._get_all_var_data() for _match, localized in branches),
        ),
    ).to(str)


def localized_request_success(value: str | rx.Var[str]) -> rx.Var[str]:
    source = rx.Var.create(value).to(str)
    template = HELP_HUB_FEEDBACK_KEYS[27]
    translated = ui(template)
    match = (
        f"String({source} ?? '').match({json.dumps(_SUCCESS_PATTERN.pattern)})"
    )
    expression = (
        f"(!String({source} ?? '') ? String({source} ?? '') : "
        f"({match} ? ({translated}).split('{{title}}').join({match}[1]) : {source}))"
    )
    return rx.Var(
        _js_expr=expression,
        _var_type=str,
        _var_data=VarData.merge(
            source._get_all_var_data(), translated._get_all_var_data()
        ),
    ).to(str)


def localized_missing_field(value: str | rx.Var[str]) -> rx.Var[str]:
    return _localized_exact(value, _MISSING_FIELD_LABELS)
