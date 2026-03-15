"""Project 3: filtering and aggregations over a validated JSON dataset."""

import json
from collections import Counter
from pathlib import Path

from flask import Blueprint, abort, current_app, request

from .validation import query_fields, query_int

bp = Blueprint("countries", __name__, url_prefix="/api/v1/countries")


def load_countries(path):
    with open(path, encoding="utf-8") as stream:
        rows = json.load(stream)
    if not isinstance(rows, list) or not rows:
        raise ValueError("Countries dataset must be a nonempty JSON array.")
    result, names = [], set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Each country must be an object.")
        name, population, languages = row.get("name"), row.get("population"), row.get("languages")
        if not isinstance(name, str) or not name.strip() or name.strip().casefold() in names:
            raise ValueError("Country names must be nonempty and unique (case-insensitive).")
        if type(population) is not int or population < 0:
            raise ValueError("Population must be a nonnegative integer.")
        if not isinstance(languages, list) or not languages or any(
            not isinstance(language, str) or not language.strip() for language in languages
        ):
            raise ValueError("Languages must be a nonempty array of nonempty strings.")
        names.add(name.strip().casefold())
        # Normalize labels so repeated spellings do not double-count a country.
        result.append({"name": name.strip(), "population": population,
                       "languages": sorted({language.strip().casefold() for language in languages})})
    return result


def init_app(app):
    configured = app.config["COUNTRIES_FILE"]
    path = configured or Path(__file__).with_name("sample_countries.json")
    app.extensions["countries"] = load_countries(path)
    app.extensions["countries_source"] = "custom" if configured else "fictional-demo"


def filtered_countries():
    name = request.args.get("name", "").strip().casefold()
    language = request.args.get("language", "").strip().casefold()
    return [row for row in current_app.extensions["countries"]
            if name in row["name"].casefold() and (not language or language in row["languages"])]


@bp.get("")
def list_countries():
    query_fields({"name", "language", "sort", "limit"})
    sort = request.args.get("sort", "name")
    if sort not in {"name", "population"}:
        abort(400, description="sort must be name or population.")
    limit = query_int("limit", 20, 250)
    rows = filtered_countries()
    key = (lambda row: row["name"].casefold()) if sort == "name" else (
        lambda row: (-row["population"], row["name"].casefold())
    )
    return {"items": sorted(rows, key=key)[:limit], "total": len(rows),
            "dataset": current_app.extensions["countries_source"]}


@bp.get("/stats")
def country_stats():
    query_fields({"name", "language", "top_n"})
    top_n = query_int("top_n", 10, 50)
    rows = filtered_countries()
    languages = Counter(language for row in rows for language in row["languages"])
    ranked = sorted(languages.items(), key=lambda item: (-item[1], item[0]))[:top_n]
    return {"country_count": len(rows), "total_population": sum(row["population"] for row in rows),
            "top_languages": [{"language": label, "country_count": count} for label, count in ranked],
            "dataset": current_app.extensions["countries_source"]}
