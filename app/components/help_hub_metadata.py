import json

import reflex as rx
from reflex.vars.base import VarData

from app.interface_i18n import ui, ui_template
from app.interface_catalog_help_hub_metadata import HELP_HUB_METADATA_CATALOGS
from app.states.auth_state import AuthState
from app.states.help_hub_state import FLEXIBLE_CHOICES, REWARD_CHOICES, WEEKDAYS


PRIVACY_SOURCE = (
    "For your privacy, users can only see your location as 0.5–1 km away "
    "from your real location. Your accurate location is only shown after "
    "you both agree on the help"
)
DATE_ERROR_SOURCES: tuple[str, ...] = (
    "Pick a date first, then press Add date.",
    "That date couldn't be read — pick it again.",
    "Choose a date from today through two calendar years from today.",
    "That date is already on your list.",
)
DURATION_UNIT_SOURCES: tuple[str, ...] = (
    "Day",
    "Days",
    "Week",
    "Weeks",
    "Month",
    "Months",
)
DURATION_UNIT_CATALOGS: dict[str, dict[str, str]] = {
    locale: {source: entries[source] for source in DURATION_UNIT_SOURCES}
    for locale, entries in HELP_HUB_METADATA_CATALOGS.items()
}


def localized_duration_unit(value: str | rx.Var[str]) -> rx.Var[str]:
    source = rx.Var.create(value).to(str)
    language = AuthState.preferred_language
    catalogs = json.dumps(DURATION_UNIT_CATALOGS, ensure_ascii=False)
    allowed_sources = json.dumps(DURATION_UNIT_SOURCES, ensure_ascii=False)
    expression = (
        f"(() => {{ const value = String({source} ?? ''); "
        f"const units = {allowed_sources}; "
        "if (!units.includes(value)) return value; "
        f"const catalogs = {catalogs}; "
        f"const locale = String({language} || 'en'); "
        "if (!Object.prototype.hasOwnProperty.call(catalogs, locale)) return value; "
        "const translations = catalogs[locale]; "
        "return Object.prototype.hasOwnProperty.call(translations, value) "
        "? translations[value] : value; })()"
    )
    return rx.Var(
        _js_expr=expression,
        _var_type=str,
        _var_data=VarData.merge(
            source._get_all_var_data(), language._get_all_var_data()
        ),
    ).to(str)


def _localized_iso_date(value: str | rx.Var[str], options: str) -> rx.Var[str]:
    source = rx.Var.create(value).to(str)
    language = AuthState.preferred_language
    expression = (
        f"(() => {{ const iso = String({source} || ''); "
        "if (!/^\\d{4}-\\d{2}-\\d{2}$/.test(iso)) return iso; "
        "const date = new Date(`${iso}T00:00:00.000Z`); "
        "if (Number.isNaN(date.getTime()) || date.toISOString().slice(0, 10) !== iso) return iso; "
        f"return new Intl.DateTimeFormat(String({language} || 'en'), "
        f"{{calendar: 'gregory', timeZone: 'UTC', {options}}}).format(date); "
        "})()"
    )
    return rx.Var(
        _js_expr=expression,
        _var_type=str,
        _var_data=VarData.merge(
            source._get_all_var_data(), language._get_all_var_data()
        ),
    ).to(str)


def localized_calendar_month(value: str | rx.Var[str]) -> rx.Var[str]:
    return _localized_iso_date(value, "month: 'long', year: 'numeric'")


def localized_calendar_accessible_date(
    value: str | rx.Var[str],
) -> rx.Var[str]:
    return _localized_iso_date(
        value,
        "weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'",
    )


def localized_date_value(value: str | rx.Var[str]) -> rx.Var[str]:
    return _localized_iso_date(
        value, "year: 'numeric', month: 'numeric', day: 'numeric'"
    )


def localized_date_trigger(value: str | rx.Var[str]) -> rx.Var[str]:
    source = rx.Var.create(value).to(str)
    fallback = ui("Choose a date")
    localized = localized_date_value(source)
    return rx.Var(
        _js_expr=f"String({source} || '') ? {localized} : {fallback}",
        _var_type=str,
        _var_data=VarData.merge(
            source._get_all_var_data(),
            fallback._get_all_var_data(),
            localized._get_all_var_data(),
        ),
    ).to(str)


def localized_date_error(value: str | rx.Var[str]) -> rx.Var[str]:
    source = rx.Var.create(value).to(str)
    cases = [(key, ui(key)) for key in DATE_ERROR_SOURCES]
    expression = f"String({source} || '')"
    for key, localized in reversed(cases):
        expression = (
            f"({expression} === {json.dumps(key, ensure_ascii=False)} "
            f"? {localized} : {expression})"
        )
    return rx.Var(
        _js_expr=expression,
        _var_type=str,
        _var_data=VarData.merge(
            source._get_all_var_data(),
            *(localized._get_all_var_data() for _key, localized in cases),
        ),
    ).to(str)


def localized_flexible_summary(
    selected: rx.Var[list[str]], custom_weekdays: rx.Var[list[str]]
) -> rx.Var[str]:
    choices = rx.Var.create(selected).to(list[str])
    custom = rx.Var.create(custom_weekdays).to(list[str])
    any_day = ui(FLEXIBLE_CHOICES[0])
    any_weekday = ui(FLEXIBLE_CHOICES[1])
    any_weekend = ui(FLEXIBLE_CHOICES[2])
    choose = ui("Choose flexible days")
    weekday_labels = [(day, ui(day)) for day in WEEKDAYS]
    custom_tokens = "".join(
        f"if (customWeekdays.includes({json.dumps(day)})) "
        f"labels.push({localized}); "
        for day, localized in weekday_labels
    )
    expression = (
        "(() => { const selected = "
        f"{choices}; const customWeekdays = {custom}; "
        f"if (selected.includes({json.dumps(FLEXIBLE_CHOICES[0])})) return {any_day}; "
        "const labels = []; "
        f"if (selected.includes({json.dumps(FLEXIBLE_CHOICES[1])})) labels.push({any_weekday}); "
        f"if (selected.includes({json.dumps(FLEXIBLE_CHOICES[2])})) labels.push({any_weekend}); "
        f"if (selected.includes({json.dumps(FLEXIBLE_CHOICES[3])})) {{ {custom_tokens} }} "
        f"return labels.join(', ') || {choose}; }})()"
    )
    return rx.Var(
        _js_expr=expression,
        _var_type=str,
        _var_data=VarData.merge(
            choices._get_all_var_data(),
            custom._get_all_var_data(),
            any_day._get_all_var_data(),
            any_weekday._get_all_var_data(),
            any_weekend._get_all_var_data(),
            choose._get_all_var_data(),
            *(
                localized._get_all_var_data()
                for _day, localized in weekday_labels
            ),
        ),
    ).to(str)


def localized_rewards_summary(selected: rx.Var[list[str]]) -> rx.Var[str]:
    selection = rx.Var.create(selected).to(list[str])
    options = [(item["value"], ui(item["label"])) for item in REWARD_CHOICES]
    value_map = (
        "{"
        + ",".join(
            f"{json.dumps(value)}: {localized}" for value, localized in options
        )
        + "}"
    )
    known_values = json.dumps([value for value, _localized in options])
    choose = ui("Choose rewards")
    count = rx.Var(
        _js_expr=(
            f"({selection}).filter(value => {known_values}.includes(value)).length"
        ),
        _var_type=int,
        _var_data=selection._get_all_var_data(),
    ).to(int)
    many = ui_template("{count} rewards selected", "count", count.to_string())
    expression = (
        f"(() => {{ const values = {selection}; "
        f"const known = {value_map}; "
        f"const labels = values.filter(value => {known_values}.includes(value))"
        ".map(value => known[value]); "
        f"if (!labels.length) return {choose}; "
        f"if (labels.length > 2) return {many}; "
        "return labels.join(', '); })()"
    )
    return rx.Var(
        _js_expr=expression,
        _var_type=str,
        _var_data=VarData.merge(
            selection._get_all_var_data(),
            *(localized._get_all_var_data() for _value, localized in options),
            choose._get_all_var_data(),
            many._get_all_var_data(),
        ),
    ).to(str)


def localized_selected_date_count(dates: rx.Var[list[str]]) -> rx.Var[str]:
    selection = rx.Var.create(dates).to(list[str])
    count = selection.length()
    empty = ui("No days chosen yet")
    singular = ui_template("{count} day chosen", "count", count.to_string())
    plural = ui_template("{count} days chosen", "count", count.to_string())
    return rx.Var(
        _js_expr=(
            f"({count} === 0 ? {empty} : "
            f"({count} === 1 ? {singular} : {plural}))"
        ),
        _var_type=str,
        _var_data=VarData.merge(
            selection._get_all_var_data(),
            empty._get_all_var_data(),
            singular._get_all_var_data(),
            plural._get_all_var_data(),
        ),
    ).to(str)


def localized_help_privacy(value: str | rx.Var[str]) -> rx.Var[str]:
    source = rx.Var.create(value).to(str)
    translation = ui(PRIVACY_SOURCE)
    return rx.Var(
        _js_expr=(
            f"String({source}) === {json.dumps(PRIVACY_SOURCE, ensure_ascii=False)} "
            f"? {translation} : {source}"
        ),
        _var_type=str,
        _var_data=VarData.merge(
            source._get_all_var_data(), translation._get_all_var_data()
        ),
    ).to(str)
