"""Versioned, display-only translations of the standard provider catalogue."""

import json
from pathlib import Path

from django.utils.translation import get_language

_CATALOG = json.loads((Path(__file__).parent / "data/exercises.pt-br.json").read_text())
CATALOG_VERSION = _CATALOG["version"]
CATALOG = {item["id"]: item for item in _CATALOG["exercises"]}
REVIEWED_TITLES = {item["title"]: item["pt_BR"] for item in CATALOG.values()}


def translated_title(title, is_custom=False, external_id=None):
    if is_custom:
        return ""
    if external_id is not None:
        entry = CATALOG.get(external_id)
        return entry["pt_BR"] if entry and entry["title"] == title else ""
    return REVIEWED_TITLES.get(title, "")


def display_name(exercise):
    if get_language() == "pt-br" and not exercise.is_custom:
        return exercise.title_pt_br or exercise.title
    return exercise.title
