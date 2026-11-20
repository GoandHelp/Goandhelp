import json

import reflex as rx
from reflex.vars.base import VarData

from app.interface_i18n import translate
from app.models import CATEGORY_LABELS, LANGUAGE_OPTIONS, TASK_CATEGORIES
from app.states.auth_state import AuthState

_PROFILE_FORM_FEEDBACK_KEYS: tuple[str, ...] = (
    "Choose at least one category, or describe your other skills and knowledge.",
    "Skills and knowledge saved.",
    "Handles are 3–30 characters, lowercase letters, numbers, dots or underscores.",
    "That biography is a little long — trim it under 2000 characters.",
    "@{handle} is already claimed by another traveller — try a different handle.",
    "@{handle} is already claimed — pick another handle.",
    "We couldn't save your profile. Please try again.",
    "Profile details saved.",
    "Your session expired — please sign in again.",
)

_PROFILE_SKILLS_CATALOGS: dict[str, dict[str, str | dict[str, str]]] = {
    locale: {
        "categories": {
            CATEGORY_LABELS[key]: translate(locale, CATEGORY_LABELS[key])
            for key in TASK_CATEGORIES
        },
        "guidance": translate(
            locale,
            "Choose the categories you can help with, and add anything else you know.",
        ),
        "empty": translate(locale, "No categories yet"),
        "plural": translate(locale, "{count} other skills listed"),
        "single": translate(locale, "1 other skill listed"),
    }
    for locale, _ in LANGUAGE_OPTIONS
}


def localized_profile_form_message(
    message: str | rx.Var[str],
) -> rx.Var[str]:
    raw = rx.Var.create(message).to(str)
    interface_text = AuthState.interface_text
    data = VarData.merge(
        raw._get_all_var_data(), interface_text._get_all_var_data()
    )
    fixed = json.dumps(_PROFILE_FORM_FEEDBACK_KEYS, ensure_ascii=False)
    expression = (
        "(() => {"
        f"const message = String({raw} || '');"
        f"const interfaceText = {interface_text};"
        f"const fixedSources = new Set({fixed});"
        "if (fixedSources.has(message)) return interfaceText[message] || message;"
        "const other = message.match(/^@([a-z0-9._]{3,30}) is already claimed by another traveller — try a different handle[.]$/);"
        "if (other) return (interfaceText['@{handle} is already claimed by another traveller — try a different handle.'] || '@{handle} is already claimed by another traveller — try a different handle.').split('{handle}').join(other[1]);"
        "const claimed = message.match(/^@([a-z0-9._]{3,30}) is already claimed — pick another handle[.]$/);"
        "if (claimed) return (interfaceText['@{handle} is already claimed — pick another handle.'] || '@{handle} is already claimed — pick another handle.').split('{handle}').join(claimed[1]);"
        "return message;"
        "})()"
    )
    return rx.Var(_js_expr=expression, _var_type=str, _var_data=data).to(str)


def localized_profile_skills_summary(
    categories: rx.Var[list[str]], skill_count: rx.Var[int]
) -> rx.Var[str]:
    category_values = rx.Var.create(categories).to(list[str])
    count_value = rx.Var.create(skill_count).to(int)
    language = AuthState.preferred_language
    catalogs = json.dumps(_PROFILE_SKILLS_CATALOGS, ensure_ascii=False)
    data = VarData.merge(
        category_values._get_all_var_data(),
        count_value._get_all_var_data(),
        language._get_all_var_data(),
    )
    expression = (
        "(() => {"
        f"const categories = {category_values};"
        f"const count = Number({count_value} || 0);"
        f"const language = {language};"
        f"const catalogs = {catalogs};"
        "const catalog = catalogs[language] || catalogs.en;"
        "const labels = categories.map(label => catalog.categories[label] || label);"
        "if (!labels.length && count === 0) return catalog.guidance;"
        "const prefix = labels.length ? labels.join(', ') : catalog.empty;"
        "if (count === 0) return prefix;"
        "const extra = count === 1 ? catalog.single : catalog.plural.replace('{count}', String(count));"
        "return `${prefix} · ${extra}`;"
        "})()"
    )
    return rx.Var(_js_expr=expression, _var_type=str, _var_data=data).to(str)
