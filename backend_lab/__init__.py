"""Three small backend projects in one Flask application."""

import os
from pathlib import Path

from flask import Flask
from werkzeug.exceptions import HTTPException

from . import countries, students, text_analyzer


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        DATABASE=os.environ.get("DATABASE_PATH", str(Path(app.instance_path) / "lab.sqlite3")),
        COUNTRIES_FILE=os.environ.get("COUNTRIES_FILE"),
        MAX_CONTENT_LENGTH=128 * 1024,
    )
    if test_config:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    students.init_app(app)
    countries.init_app(app)
    app.register_blueprint(text_analyzer.bp)
    app.register_blueprint(students.bp)
    app.register_blueprint(countries.bp)

    @app.get("/health")
    def health():
        return {"status": "ok", "projects": ["text-analyzer", "student-records", "countries-insights"]}

    @app.errorhandler(HTTPException)
    def http_error(error):
        response = error.get_response()
        response.data = app.json.dumps({"error": {"code": error.code, "message": error.description}})
        response.content_type = "application/json"
        return response

    return app
