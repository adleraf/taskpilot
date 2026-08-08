import os
from datetime import datetime, date

from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tasks.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    priority = db.Column(db.String(20), default="Medium")
    due_date = db.Column(db.String(50))

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def _get_owned_task_or_404(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        abort(403)
    return task


@app.route("/", methods=["GET", "POST"])
@login_required
def home():
    if request.method == "POST":
        title = request.form.get("task", "").strip()
        priority = request.form.get("priority", "Medium")
        due_date = request.form.get("due_date", "")

        if not title:
            flash("Task title can't be empty!", "danger")
            return redirect(url_for("home"))

        if due_date:
            try:
                selected_date = datetime.strptime(due_date, "%Y-%m-%d").date()
            except ValueError:
                flash("Invalid due date format!", "danger")
                return redirect(url_for("home"))

            if selected_date < date.today():
                flash("You cannot choose a past due date!", "danger")
                return redirect(url_for("home"))

        new_task = Task(
            title=title,
            priority=priority,
            due_date=due_date,
            user_id=current_user.id,
        )
        db.session.add(new_task)
        db.session.commit()
        flash("Task added successfully!", "success")

        return redirect(url_for("home"))

    search = request.args.get("search")

    all_tasks = Task.query.filter_by(user_id=current_user.id).all()
    total_tasks = len(all_tasks)
    completed_tasks = len([task for task in all_tasks if task.completed])
    pending_tasks = total_tasks - completed_tasks
    progress = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0

    tasks = all_tasks
    if search:
        tasks = [task for task in all_tasks if search.lower() in task.title.lower()]

    today = date.today().strftime("%Y-%m-%d")

    return render_template(
        "index.html",
        tasks=tasks,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        progress=progress,
        today=today,
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not username or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for("register"))

        if User.query.filter_by(email=email).first():
            flash("Email already exists!", "danger")
            return redirect(url_for("register"))

        if User.query.filter_by(username=username).first():
            flash("Username already exists!", "danger")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(url_for("home"))

        flash("Invalid email or password", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/toggle/<int:id>", methods=["POST"])
@login_required
def toggle(id):
    task = _get_owned_task_or_404(id)
    task.completed = not task.completed
    db.session.commit()
    flash("Task updated!", "success")
    return redirect(url_for("home"))


@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit(id):
    task = _get_owned_task_or_404(id)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            flash("Task title can't be empty!", "danger")
            return redirect(url_for("edit", id=id))

        task.title = title
        db.session.commit()
        flash("Task updated!", "success")
        return redirect(url_for("home"))

    return render_template("edit.html", task=task)


@app.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete(id):
    task = _get_owned_task_or_404(id)
    db.session.delete(task)
    db.session.commit()
    flash("Task deleted!", "danger")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
