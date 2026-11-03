import os
import sqlite3
from pathlib import Path

from flask import Flask, flash, g, redirect, render_template, request, url_for


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

    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(_error=None):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    def init_db():
        db = get_db()
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
        db.commit()

    with app.app_context():
        init_db()

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/contact")
    def contact():
        if request.form.get("website"):
            return redirect(url_for("index", sent="1") + "#contact")

        fields = {key: request.form.get(key, "").strip() for key in ("name", "email", "subject", "message")}
        errors = []
        if not fields["name"] or len(fields["name"]) > 80:
            errors.append("お名前は80文字以内で入力してください。")
        if not fields["email"] or "@" not in fields["email"] or len(fields["email"]) > 254:
            errors.append("有効なメールアドレスを入力してください。")
        if not fields["subject"] or len(fields["subject"]) > 120:
            errors.append("件名は120文字以内で入力してください。")
        if not fields["message"] or len(fields["message"]) > 2000:
            errors.append("お問い合わせ内容は2000文字以内で入力してください。")
        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("index.html", form=fields), 400

        db = get_db()
        db.execute(
            "INSERT INTO inquiries (name, email, subject, message) VALUES (?, ?, ?, ?)",
            (fields["name"], fields["email"], fields["subject"], fields["message"]),
        )
        db.commit()
        flash("お問い合わせを受け付けました。ありがとうございます。", "success")
        return redirect(url_for("index", sent="1") + "#contact")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
