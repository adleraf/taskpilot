from datetime import datetime, date
from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
)
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

app.config["SECRET_KEY"] = "taskpilot-super-secret-key"

# Database Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tasks.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = "login"

class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(120), unique=True, nullable=False)

    password = db.Column(db.String(255), nullable=False)



class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    priority = db.Column(db.String(20), default="Medium")
    due_date = db.Column(db.String(50))


with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/", methods=["GET", "POST"])
@login_required
def home():

    if request.method == "POST":

        title = request.form["task"]
        priority = request.form["priority"]
        due_date = request.form["due_date"]

        # Check if the selected date is in the past
        selected_date = datetime.strptime(due_date, "%Y-%m-%d").date()

        if selected_date < date.today():
            flash("❌ You cannot choose a past due date!", "danger")
            return redirect("/")

        if title.strip():

            new_task = Task(
                title=title,
                priority=priority,
                due_date=due_date
            )

            db.session.add(new_task)
            db.session.commit()

            flash("✅ Task added successfully!", "success")

        return redirect("/")

    # Search
    search = request.args.get("search")

    if search:
        tasks = Task.query.filter(
            Task.title.ilike(f"%{search}%")
        ).all()
    else:
        tasks = Task.query.all()

    # Dashboard stats
    total_tasks = len(tasks)
    completed_tasks = len([task for task in tasks if task.completed])
    pending_tasks = total_tasks - completed_tasks

    if total_tasks > 0:
        progress = int((completed_tasks / total_tasks) * 100)
    else:
        progress = 0

    # Today's date for the HTML date picker
    today = date.today().strftime("%Y-%m-%d")

    return render_template(
        "index.html",
        tasks=tasks,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        progress=progress,
        today=today
    )

    
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            return "Email already exists!"

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Create user
        new_user = User(
            username=username,
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        flash("🎉 Account created successfully! Please login.", "success")

        return redirect("/login")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):

            login_user(user)

            flash(f"👋 Welcome back, {user.username}!", "success")

            return redirect("/")

        return "Invalid email or password"

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():

    logout_user()

    flash("👋 You have been logged out.", "info")

    return redirect("/login")


@app.route("/toggle/<int:id>")
def toggle(id):

    task = Task.query.get_or_404(id)

    task.completed = not task.completed

    db.session.commit()

    flash("🎉 Task updated!", "success")

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

    flash("🗑️ Task deleted!", "danger")

    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)