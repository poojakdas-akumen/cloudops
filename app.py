import os
import sqlite3
from pathlib import Path
from flask import Flask, abort, flash, g, jsonify, redirect, render_template, request, url_for

def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "change-this-in-production"),
        DATABASE=os.environ.get("DATABASE_PATH", str(Path(app.instance_path) / "tasks.sqlite3")),
    )
    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    def get_db():
        if "db" not in g:
            db_path = app.config["DATABASE"]
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            g.db = sqlite3.connect(db_path)
            g.db.row_factory = sqlite3.Row
            g.db.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    owner TEXT NOT NULL DEFAULT '',
                    priority TEXT NOT NULL DEFAULT 'Medium',
                    status TEXT NOT NULL DEFAULT 'Pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            g.db.commit()
        return g.db

    @app.teardown_appcontext
    def close_db(exception=None):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    @app.get("/")
    def index():
        status = request.args.get("status", "")
        allowed = {"Pending", "In Progress", "Completed"}
        db = get_db()
        if status in allowed:
            tasks = db.execute("SELECT * FROM tasks WHERE status=? ORDER BY id DESC", (status,)).fetchall()
        else:
            status = ""
            tasks = db.execute("SELECT * FROM tasks ORDER BY id DESC").fetchall()
        stats = {
            "total": db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0],
            "pending": db.execute("SELECT COUNT(*) FROM tasks WHERE status='Pending'").fetchone()[0],
            "progress": db.execute("SELECT COUNT(*) FROM tasks WHERE status='In Progress'").fetchone()[0],
            "completed": db.execute("SELECT COUNT(*) FROM tasks WHERE status='Completed'").fetchone()[0],
        }
        return render_template("index.html", tasks=tasks, stats=stats, selected_status=status)

    @app.post("/tasks")
    def create_task():
        title = request.form.get("title", "").strip()
        if not title:
            flash("Task title is required.", "error")
            return redirect(url_for("index"))
        priority = request.form.get("priority", "Medium")
        if priority not in {"Low", "Medium", "High"}:
            priority = "Medium"
        get_db().execute(
            "INSERT INTO tasks (title, description, owner, priority) VALUES (?, ?, ?, ?)",
            (title[:120], request.form.get("description", "").strip()[:1000],
             request.form.get("owner", "").strip()[:80], priority),
        )
        get_db().commit()
        flash("Task created successfully.", "success")
        return redirect(url_for("index"))

    @app.post("/tasks/<int:task_id>/status")
    def update_status(task_id):
        status = request.form.get("status")
        if status not in {"Pending", "In Progress", "Completed"}:
            abort(400)
        cursor = get_db().execute("UPDATE tasks SET status=? WHERE id=?", (status, task_id))
        get_db().commit()
        if cursor.rowcount == 0:
            abort(404)
        flash("Task status updated.", "success")
        return redirect(url_for("index"))

    @app.post("/tasks/<int:task_id>/delete")
    def delete_task(task_id):
        cursor = get_db().execute("DELETE FROM tasks WHERE id=?", (task_id,))
        get_db().commit()
        if cursor.rowcount == 0:
            abort(404)
        flash("Task deleted.", "success")
        return redirect(url_for("index"))

    @app.get("/health")
    def health():
        get_db().execute("SELECT 1").fetchone()
        return jsonify(status="healthy", application="CloudOps Task Manager"), 200

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
