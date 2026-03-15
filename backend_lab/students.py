"""Project 2: SQLite-backed student records with parameterized queries."""

import json
import sqlite3
from datetime import datetime, timezone

from flask import Blueprint, abort, current_app, g, request, url_for

from .validation import json_object, query_fields, query_int

bp = Blueprint("students", __name__, url_prefix="/api/v1/students")
FIELDS = {"name", "country", "city", "birth_year", "skills", "bio"}
SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    country TEXT NOT NULL DEFAULT '',
    city TEXT NOT NULL DEFAULT '',
    birth_year INTEGER,
    skills TEXT NOT NULL DEFAULT '[]',
    bio TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"], timeout=10)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        db = get_db()
        db.executescript(SCHEMA)
        db.commit()


def serialize(row):
    data = dict(row)
    data["skills"] = json.loads(data["skills"])
    return data


def get_student(student_id):
    if student_id > 2**63 - 1:
        abort(404, description="Student not found.")
    row = get_db().execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    if row is None:
        abort(404, description="Student not found.")
    return serialize(row)


def validate(data, partial=False):
    if not data or set(data) - FIELDS:
        abort(400, description="Provide at least one supported student field.")
    if not partial and "name" not in data:
        abort(400, description="name is required.")
    clean = {}
    for field, value in data.items():
        if field == "birth_year":
            if value is not None and (
                type(value) is not int or not 1900 <= value <= datetime.now(timezone.utc).year
            ):
                abort(400, description="birth_year must be null or an integer from 1900 through this year.")
        elif field == "skills":
            if not isinstance(value, list) or len(value) > 30 or any(
                not isinstance(skill, str) or not skill.strip() or len(skill) > 80 for skill in value
            ):
                abort(400, description="skills must be an array of up to 30 nonempty strings (80 characters each).")
            value = list(dict.fromkeys(skill.strip() for skill in value))
        else:
            limit = 2000 if field == "bio" else 120
            if not isinstance(value, str) or len(value) > limit or (field == "name" and not value.strip()):
                abort(400, description=f"{field} must be a string of at most {limit} characters; name cannot be blank.")
            value = value.strip()
        clean[field] = value
    return clean


@bp.post("")
def create_student():
    data = {"country": "", "city": "", "birth_year": None, "skills": [], "bio": ""}
    data.update(validate(json_object()))
    now = datetime.now(timezone.utc).isoformat()
    db = get_db()
    with db:
        cursor = db.execute(
            "INSERT INTO students (name, country, city, birth_year, skills, bio, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (data["name"], data["country"], data["city"], data["birth_year"], json.dumps(data["skills"]), data["bio"], now, now),
        )
    return get_student(cursor.lastrowid), 201, {"Location": url_for("students.read_student", student_id=cursor.lastrowid)}


@bp.get("")
def list_students():
    query_fields({"page", "per_page", "country"})
    page, per_page = query_int("page", 1, 1_000_000), query_int("per_page", 20, 100)
    country = request.args.get("country")
    where, params = (" WHERE country = ? COLLATE NOCASE", [country.strip()]) if country is not None else ("", [])
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM students" + where, params).fetchone()[0]
    rows = db.execute(
        "SELECT * FROM students" + where + " ORDER BY id LIMIT ? OFFSET ?",
        [*params, per_page, (page - 1) * per_page],
    ).fetchall()
    return {"items": [serialize(row) for row in rows], "total": total, "page": page, "per_page": per_page}


@bp.get("/<int:student_id>")
def read_student(student_id):
    return get_student(student_id)


@bp.patch("/<int:student_id>")
def update_student(student_id):
    get_student(student_id)
    data = validate(json_object(), partial=True)
    if "skills" in data:
        data["skills"] = json.dumps(data["skills"])
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    # Column names come only from the allowlist in validate(); values are bound.
    assignments = ", ".join(f"{field} = ?" for field in data)
    db = get_db()
    with db:
        db.execute(f"UPDATE students SET {assignments} WHERE id = ?", [*data.values(), student_id])
    return get_student(student_id)


@bp.delete("/<int:student_id>")
def delete_student(student_id):
    if student_id > 2**63 - 1:
        abort(404, description="Student not found.")
    db = get_db()
    with db:
        cursor = db.execute("DELETE FROM students WHERE id = ?", (student_id,))
        if cursor.rowcount == 0:
            abort(404, description="Student not found.")
    return "", 204
