from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tasks.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)


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

    tasks = Task.query.all()

    return render_template("index.html", tasks=tasks)


@app.route("/delete/<int:id>")
def delete(id):

    task = Task.query.get_or_404(id)

    db.session.delete(task)

    db.session.commit()

    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)