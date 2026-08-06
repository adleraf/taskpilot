from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tasks.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)


with app.app_context():
    db.create_all()


@app.route("/", methods=["GET", "POST"])
def home():

    if request.method == "POST":
        title = request.form["task"]

        if title.strip():
            new_task = Task(title=title)
            db.session.add(new_task)
            db.session.commit()

        return redirect("/")

    # Get all tasks
    tasks = Task.query.all()

    # Dashboard statistics
    total_tasks = len(tasks)
    completed_tasks = len([task for task in tasks if task.completed])
    pending_tasks = total_tasks - completed_tasks

    if total_tasks > 0:
        progress = int((completed_tasks / total_tasks) * 100)
    else:
        progress = 0

    return render_template(
        "index.html",
        tasks=tasks,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        progress=progress
    )


@app.route("/toggle/<int:id>")
def toggle(id):
    task = Task.query.get_or_404(id)

    task.completed = not task.completed

    db.session.commit()

    return redirect("/")


@app.route("/delete/<int:id>")
def delete(id):
    task = Task.query.get_or_404(id)

    db.session.delete(task)

    db.session.commit()

    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)