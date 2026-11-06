"""Schema validation against the plugin's JSON Schemas (draft 2020-12)."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

SCHEMAS = Path(__file__).resolve().parents[2] / "schemas"


@lru_cache(maxsize=1)
def _registry() -> tuple[Registry, dict]:
    docs, reg = {}, Registry()
    for p in SCHEMAS.glob("*.json"):
        doc = json.loads(p.read_text())
        docs[p.stem] = doc
        res = Resource.from_contents(doc)
        reg = reg.with_resources([(p.name, res), (p.stem, res)])
    return reg, docs


def errors(name: str, obj) -> list[str]:
    reg, docs = _registry()
    v = Draft202012Validator(docs[name], registry=reg, format_checker=FormatChecker())
    return [f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}" for e in v.iter_errors(obj)]


def validate(name: str, obj) -> None:
    errs = errors(name, obj)
    if errs:
        raise ValueError(f"{name} validation failed: " + "; ".join(errs[:10]))
