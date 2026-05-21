#!/usr/bin/env python3
"""Valide les frontmatters YAML des recettes _recipes/*.md.

Le schéma reflète la structure attendue par les templates Jekyll et la
config Decap CMS (admin/config.yml). Il refuse en particulier la
structure imbriquée `group/items` dans les ingrédients (ancien format)
et les champs vides sur les zones critiques.

Usage local :
    pip install pyyaml jsonschema
    python scripts/validate_recipes.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


INGREDIENT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["qty", "name"],
    "properties": {
        "qty": {"type": "string", "minLength": 1},
        "name": {"type": "string", "minLength": 1},
        "note": {"type": ["string", "null"]},
    },
}

STEP_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["title", "body"],
    "properties": {
        "title": {"type": "string", "minLength": 1},
        "body": {"type": "string", "minLength": 1},
    },
}

TIP_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["title", "body"],
    "properties": {
        "title": {"type": "string", "minLength": 1},
        "body": {"type": "string", "minLength": 1},
    },
}

RECIPE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["title", "slug", "ingredients", "steps"],
    "properties": {
        "title": {"type": "string", "minLength": 1},
        "slug": {
            "type": "string",
            "pattern": r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        },
        "kicker": {"type": ["string", "null"]},
        "subtitle": {"type": ["string", "null"]},
        "serie": {
            "type": ["object", "null"],
            "additionalProperties": False,
            "properties": {
                "name": {"type": ["string", "null"]},
                "episode": {"type": ["string", "null"]},
            },
        },
        "time": {"type": ["string", "null"]},
        "servings": {"type": ["integer", "null"]},
        "season": {"enum": ["Printemps", "Été", "Automne", "Hiver", None]},
        "difficulty": {"enum": ["1", "2", "3", "4", "5", None]},
        "chef": {
            "type": ["object", "null"],
            "additionalProperties": False,
            "properties": {
                "name": {"type": ["string", "null"]},
                "restaurant": {"type": ["string", "null"]},
                "photo": {"type": ["string", "null"]},
                "bio": {"type": ["string", "null"]},
            },
        },
        "image": {"type": ["string", "null"]},
        "image_credit": {"type": ["string", "null"]},
        "ingredients": {
            "type": "array",
            "minItems": 1,
            "items": INGREDIENT_SCHEMA,
        },
        "steps": {
            "type": "array",
            "minItems": 1,
            "items": STEP_SCHEMA,
        },
        "quote": {
            "type": ["object", "null"],
            "additionalProperties": False,
            "properties": {
                "text": {"type": ["string", "null"]},
                "author": {"type": ["string", "null"]},
            },
        },
        "tips": {
            "type": ["array", "null"],
            "items": TIP_SCHEMA,
        },
        "wine": {
            "type": ["object", "null"],
            "additionalProperties": False,
            "properties": {
                "label": {"type": ["string", "null"]},
                "name": {"type": ["string", "null"]},
                "description": {"type": ["string", "null"]},
            },
        },
        "nav": {
            "type": ["object", "null"],
            "additionalProperties": False,
            "properties": {
                "prev_label": {"type": ["string", "null"]},
                "prev_text": {"type": ["string", "null"]},
                "next_label": {"type": ["string", "null"]},
                "next_text": {"type": ["string", "null"]},
                "current": {"type": ["integer", "null"]},
                "total": {"type": ["integer", "null"]},
            },
        },
    },
}


def parse_frontmatter(text: str):
    """Renvoie le frontmatter YAML d'un fichier Markdown, ou None."""
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    return yaml.safe_load(parts[1]) or {}


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    recipes_dir = repo_root / "_recipes"
    if not recipes_dir.is_dir():
        print(f"[!] Dossier _recipes/ introuvable ({recipes_dir})", file=sys.stderr)
        return 1

    validator = Draft202012Validator(RECIPE_SCHEMA)
    files = sorted(recipes_dir.glob("*.md"))
    if not files:
        print("[i] Aucune recette à valider.")
        return 0

    total_errors = 0
    for path in files:
        rel = path.relative_to(repo_root)
        text = path.read_text(encoding="utf-8")
        data = parse_frontmatter(text)
        if data is None:
            print(f"[KO] {rel} : frontmatter YAML manquant ou malformé")
            total_errors += 1
            continue
        errors = sorted(validator.iter_errors(data), key=lambda e: [str(p) for p in e.absolute_path])
        if not errors:
            print(f"[OK] {rel}")
            continue
        for err in errors:
            loc = "/".join(str(p) for p in err.absolute_path) or "<racine>"
            print(f"[KO] {rel} : {loc} — {err.message}")
            total_errors += 1

    if total_errors:
        print(f"\n{total_errors} erreur(s) de validation.", file=sys.stderr)
        return 1
    print(f"\n{len(files)} recette(s) validée(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
