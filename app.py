from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Database Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tasks.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ==========================
# Database Model
# ==========================

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    priority = db.Column(db.String(20), default="Medium")
    due_date = db.Column(db.String(50))


with app.app_context():
    db.create_all()




@app.route("/", methods=["GET", "POST"])
def home():

    
    if request.method == "POST":

        title = request.form["task"]
        priority = request.form["priority"]
        due_date = request.form["due_date"]

        if title.strip():

            new_task = Task(
                title=title,
                priority=priority,
                due_date=due_date
            )

            db.session.add(new_task)
            db.session.commit()

        return redirect("/")

    
    search = request.args.get("search")

    if search:
        tasks = Task.query.filter(
            Task.title.ilike(f"%{search}%")
        ).all()
    else:
        tasks = Task.query.all()

   
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



@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):

    task = Task.query.get_or_404(id)

    if request.method == "POST":

        task.title = request.form["title"]

        db.session.commit()

        return redirect("/")

    return render_template("edit.html", task=task)



@app.route("/delete/<int:id>")
def delete(id):

    task = Task.query.get_or_404(id)

    db.session.delete(task)

    db.session.commit()

    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)