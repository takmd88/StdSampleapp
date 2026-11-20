import os
import sqlite3
from pathlib import Path

from flask import Flask, current_app, flash, g, redirect, render_template, request, url_for


CONTACT_FIELDS = (
    ("name", 80, "お名前は80文字以内で入力してください。"),
    ("email", 254, "有効なメールアドレスを入力してください。"),
    ("subject", 120, "件名は120文字以内で入力してください。"),
    ("message", 2000, "お問い合わせ内容は2000文字以内で入力してください。"),
)


def get_db():
    """Reuse one database connection per application context."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS inquiries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                subject TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)


def validate_contact(form):
    fields = {}
    errors = []
    for key, max_length, error in CONTACT_FIELDS:
        value = form.get(key, "").strip()
        fields[key] = value
        if not value or len(value) > max_length or (key == "email" and "@" not in value):
            errors.append(error)
    return fields, errors


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
        DATABASE=str(Path(app.instance_path) / "portfolio.db"),
        MAX_CONTENT_LENGTH=32 * 1024,
    )
    if test_config:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    app.teardown_appcontext(close_db)

    with app.app_context():
        init_db()

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/contact")
    def contact():
        if request.form.get("website"):
            return redirect(url_for("index", sent="1", _anchor="contact"))

        fields, errors = validate_contact(request.form)
        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("index.html", form=fields), 400

        with get_db() as db:
            db.execute(
                """INSERT INTO inquiries (name, email, subject, message)
                   VALUES (:name, :email, :subject, :message)""",
                fields,
            )
        flash("お問い合わせを受け付けました。ありがとうございます。", "success")
        return redirect(url_for("index", sent="1", _anchor="contact"))

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
