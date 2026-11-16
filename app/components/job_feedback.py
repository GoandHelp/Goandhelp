import json
import re

import reflex as rx
from reflex.vars.base import VarData

from app.interface_catalog_job_feedback import JOB_FEEDBACK_LITERAL_KEYS
from app.interface_i18n import ui
from app.states.auth_state import AuthState


_JOB_FEEDBACK_TEMPLATES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Accepted — you're helping with “{title}”.", ("title",)),
    (
        "{added} photo(s) added. {skipped} were skipped — five photos per story, common image formats only.",
        ("added", "skipped"),
    ),
    ("{added} photo(s) added to your story.", ("added",)),
    ("Preparing your {network_label} share…", ("network_label",)),
)


def _template_regex(source: str, slots: tuple[str, ...]) -> str:
    escaped = re.escape(source)
    for slot in slots:
        slot_expression = re.escape(f"{{{slot}}}")
        capture = r"(\d+)" if slot in {"added", "skipped"} else r"([\s\S]*?)"
        escaped = escaped.replace(slot_expression, capture, 1)
    return f"^{escaped}$"


def job_feedback(message: rx.Var[str] | str) -> rx.Var[str]:
    source = rx.Var.create(message).to(str)
    exact = AuthState.interface_text.get(source, source).to(str)
    patterns = [
        {
            "source": template,
            "regex": _template_regex(template, slots),
            "slots": slots,
        }
        for template, slots in _JOB_FEEDBACK_TEMPLATES
    ]
    localized_templates = [
        ui(template).to(str) for template, _slots in _JOB_FEEDBACK_TEMPLATES
    ]
    branches = []
    for index, pattern in enumerate(patterns):
        values = (
            "{"
            + ",".join(
                f"{json.dumps(slot)}: match[{slot_index + 1}]"
                for slot_index, slot in enumerate(pattern["slots"])
            )
            + "}"
        )
        template_value = localized_templates[index]
        branch = (
            f"((match = new RegExp({json.dumps(pattern['regex'])}).exec(source))"
            f" ? {template_value}.replace(/\\{{(added|skipped|title|network_label)\\}}/g, "
            f"(_token, slot) => Object.prototype.hasOwnProperty.call({values}, slot) ? {values}[slot] : _token) : null)"
        )
        branches.append(branch)
    literal_keys = json.dumps(JOB_FEEDBACK_LITERAL_KEYS, ensure_ascii=False)
    expression = (
        "(() => { const source = "
        f"{source}; let match; const translated = "
        + " ?? ".join(branches)
        + f"; if (translated !== null) return translated; "
        f"if ({literal_keys}.includes(source)) return {exact}; "
        "return source; })()"
    )
    data = VarData.merge(
        source._get_all_var_data(),
        exact._get_all_var_data(),
        *(template._get_all_var_data() for template in localized_templates),
    )
    return rx.Var(_js_expr=expression, _var_type=str, _var_data=data).to(str)
