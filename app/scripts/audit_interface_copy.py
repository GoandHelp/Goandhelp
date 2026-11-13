import reflex as rx

import argparse
import ast
import logging
import re
from pathlib import Path

from app.interface_i18n import CATALOGS
from app.models import LANGUAGE_OPTIONS

VISIBLE_ELEMENTS = {
    "p",
    "span",
    "h1",
    "h2",
    "h3",
    "h4",
    "label",
    "legend",
    "button",
    "summary",
    "option",
    "a",
    "li",
    "th",
    "td",
}
VISIBLE_PROPS = {"placeholder", "aria_label", "title", "alt"}
EXAMPLES_AND_BRANDS = {
    "Go and Help",
    "Goandhelp",
    "Maya",
    "De Silva",
    "Porto",
    "Portugal",
    "Portuguese",
    "you@example.com",
    "maya.lisbon",
    "your.username",
    "UTC",
}


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_call_name(node.value)}.{node.attr}"
    return ""


def _visible_literals(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, ast.Call):
        name = _call_name(node.func)
        if name == "rx.cond":
            return [
                text
                for arg in node.args[1:3]
                for text in _visible_literals(arg)
            ]
        if name == "rx.match":
            result: list[str] = []
            for branch in node.args[1:]:
                value = (
                    branch.elts[1]
                    if isinstance(branch, ast.Tuple) and len(branch.elts) == 2
                    else branch
                )
                result.extend(_visible_literals(value))
            return result
    return []


def _candidate(source: str) -> bool:
    return (
        bool(re.search(r"[A-Za-z]", source))
        and source not in EXAMPLES_AND_BRANDS
    )


def analyze_source(source: str) -> list[dict[str, str | int | list[str]]]:
    """Static candidates only. Never evaluates code or reads member records."""
    findings: list[dict[str, str | int | list[str]]] = []
    languages = [code for code, _ in LANGUAGE_OPTIONS if code != "en"]
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node.func)
        if name == "ui":
            for arg in node.args[:1]:
                for phrase in _visible_literals(arg):
                    missing = [
                        code
                        for code in languages
                        if phrase not in CATALOGS[code]
                    ]
                    if missing:
                        findings.append(
                            {
                                "line": node.lineno,
                                "kind": "catalog gap",
                                "source": phrase,
                                "missing": missing,
                            }
                        )
            continue
        nodes: list[ast.AST] = []
        if (
            name.startswith("rx.el.")
            and name.rsplit(".", 1)[-1] in VISIBLE_ELEMENTS
        ):
            nodes.extend(node.args)
        if name in {"field_label", "small_label"}:
            nodes.extend(node.args[:2])
        if name.startswith("rx.el.") or name == "rx.image":
            nodes.extend(
                keyword.value
                for keyword in node.keywords
                if keyword.arg in VISIBLE_PROPS
            )
        for argument in nodes:
            for phrase in _visible_literals(argument):
                if _candidate(phrase):
                    missing = [
                        code
                        for code in languages
                        if phrase not in CATALOGS[code]
                    ]
                    findings.append(
                        {
                            "line": node.lineno,
                            "kind": "raw copy",
                            "source": phrase,
                            "missing": missing,
                        }
                    )
            if isinstance(argument, ast.JoinedStr):
                fragments = " … ".join(
                    part.value
                    for part in argument.values
                    if isinstance(part, ast.Constant)
                    and isinstance(part.value, str)
                )
                if _candidate(fragments):
                    findings.append(
                        {
                            "line": node.lineno,
                            "kind": "template audit",
                            "source": fragments,
                            "missing": [],
                        }
                    )
    return findings


def audit_paths(paths: list[Path]) -> list[dict[str, str | int | list[str]]]:
    findings: list[dict[str, str | int | list[str]]] = []
    for path in paths:
        try:
            for finding in analyze_source(path.read_text(encoding="utf-8")):
                findings.append({**finding, "path": str(path)})
        except Exception as e:
            logging.exception(f"Error: {e}")
            raise
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Offline static interface-copy audit; no member data or translation services."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail when any static candidate needs audit.",
    )
    args = parser.parse_args()
    paths = sorted(Path("app/components").glob("*.py"))
    paths.append(Path("app/app.py"))
    findings = audit_paths(paths)
    print("# Offline interface-copy audit candidates")
    print(
        "\nThis is not an exhaustive or linguistic sign-off. Dynamic metadata, helper arguments, state feedback, embedded map controls and responsive/browser behavior still require manual review.\n"
    )
    for finding in findings:
        phrase = str(finding["source"]).replace("\n", " ").replace("|", "\\|")
        missing = ", ".join(finding["missing"])
        print(
            f"- {finding['path']}:{finding['line']} — {finding['kind']}: {phrase} — missing locales: {missing or 'none'}"
        )
    print(f"\n{len(findings)} candidates; member records were not accessed.")
    return 1 if args.strict and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
