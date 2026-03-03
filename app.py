from flask import Flask, render_template, redirect, url_for, request,flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import csv
from flask_login import logout_user
from flask import redirect, url_for


app = Flask(__name__)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SECRET_KEY"] = "secretkey"

db = SQLAlchemy(app)

# --------------------
# User Model
# --------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Food(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    calories = db.Column(db.Integer, nullable=False)
    protein = db.Column(db.Float, nullable=False)
    carbs = db.Column(db.Float, nullable=False)
    fat = db.Column(db.Float, nullable=False)

class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Float, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    food_id = db.Column(db.Integer, db.ForeignKey("food.id"), nullable=False)
    food = db.relationship("Food")
# --------------------
# Home Route
# --------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists!","danger")
            return redirect(url_for("register"))

        # Create new user
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return "User registered successfully!"

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password","danger")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():

    if request.method == "POST":
        food_id = request.form.get("food_id")
        quantity = float(request.form.get("quantity"))

        new_meal = Meal(
            user_id=current_user.id,
            food_id=food_id,
            quantity=quantity
        )

        db.session.add(new_meal)
        db.session.commit()
        return redirect("/dashboard")

    meals = Meal.query.filter_by(user_id=current_user.id).all()
    foods = Food.query.all()

    total_calories = 0
    total_protein = 0
    total_carbs = 0
    total_fat = 0

    for meal in meals:
        total_calories += meal.food.calories * meal.quantity
        total_protein += meal.food.protein * meal.quantity
        total_carbs += meal.food.carbs * meal.quantity
        total_fat += meal.food.fat * meal.quantity

    return render_template(
        "dashboard.html",
        meals=meals,
        foods=foods,
        total_calories=total_calories,
        total_protein=total_protein,
        total_carbs=total_carbs,
        total_fat=total_fat
    )

@app.route("/delete_meal/<int:meal_id>")
@login_required
def delete_meal(meal_id):
    meal = Meal.query.get_or_404(meal_id)

    # Security check → user can delete only their own meal
    if meal.user_id != current_user.id:
        return "Unauthorized action"

    db.session.delete(meal)
    db.session.commit()

    return redirect(url_for("dashboard"))


@app.route("/")
def home():
    return redirect(url_for("register"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        if Food.query.count() == 0:
            with open("food_data.csv", newline="") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    food = Food(
                        name=row["name"],
                        calories=int(row["calories"]),
                        protein=float(row["protein"]),
                        carbs=float(row["carbs"]),
                        fat=float(row["fat"])
                    )
                    db.session.add(food)

                db.session.commit()

    app.run(debug=True)