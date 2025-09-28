import os
from datetime import date
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from .extensions import db, login_manager
from .models import User, Shift, Trip, Expense

def create_app():
    app = Flask(__name__)

    # Ensure instance dir for sqlite persistence
    instance_dir = os.path.join(os.getcwd(), "instance")
    os.makedirs(instance_dir, exist_ok=True)

    secret = os.getenv("SECRET_KEY", "change-me")
    db_file = os.getenv("DB_FILE", "flex.db")
    app.config.update(
        SECRET_KEY=secret,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{os.path.join(instance_dir, db_file)}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "login"

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # --- Auto create DB schema on first run ---
    with app.app_context():
        db.create_all()

    # Routes
    @app.get("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        return render_template("index.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            if not email or not password:
                flash("Informe email e senha.", "warning")
                return redirect(url_for("register"))
            if db.session.query(User).filter_by(email=email).first():
                flash("Email já cadastrado.", "danger")
                return redirect(url_for("register"))
            u = User(email=email)
            u.set_password(password)
            db.session.add(u)
            db.session.commit()
            flash("Conta criada. Faça login.", "success")
            return redirect(url_for("login"))
        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            u = db.session.query(User).filter_by(email=email).first()
            if u and u.check_password(password):
                login_user(u)
                return redirect(url_for("dashboard"))
            flash("Credenciais inválidas.", "danger")
        return render_template("login.html")

    @app.get("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("index"))

    @app.get("/dashboard")
    @login_required
    def dashboard():
        total_shifts = db.session.query(Shift).count()
        total_trips = db.session.query(Trip).count()
        total_fare = db.session.query(db.func.coalesce(db.func.sum(Trip.fare_amount), 0.0)).scalar()
        total_tips = db.session.query(db.func.coalesce(db.func.sum(Trip.tips), 0.0)).scalar()
        total_fuel = db.session.query(db.func.coalesce(db.func.sum(Trip.fuel_cost), 0.0)).scalar()
        total_expenses = db.session.query(db.func.coalesce(db.func.sum(Expense.amount), 0.0)).scalar()
        return render_template("dashboard.html",
                               totals=dict(shifts=total_shifts, trips=total_trips, fare=total_fare,
                                           tips=total_tips, fuel=total_fuel, expenses=total_expenses))

    @app.route("/shift/new", methods=["GET", "POST"])
    @login_required
    def shift_new():
        if request.method == "POST":
            d = request.form.get("date") or date.today().isoformat()
            hours = float(request.form.get("hours_worked") or 0)
            s = Shift(date=d, hours_worked=hours)
            db.session.add(s)
            db.session.commit()
            return redirect(url_for("dashboard"))
        return render_template("shift_form.html")

    @app.route("/trip/new", methods=["GET", "POST"])
    @login_required
    def trip_new():
        if request.method == "POST":
            shift_id = int(request.form.get("shift_id"))
            fare = float(request.form.get("fare_amount") or 0)
            fuel = float(request.form.get("fuel_cost") or 0)
            odo = float(request.form.get("odometer") or 0)
            tips = float(request.form.get("tips") or 0)
            t = Trip(shift_id=shift_id, fare_amount=fare, fuel_cost=fuel, odometer=odo, tips=tips)
            db.session.add(t)
            db.session.commit()
            return redirect(url_for("dashboard"))
        shifts = db.session.query(Shift).order_by(Shift.date.desc()).all()
        return render_template("trip_form.html", shifts=shifts)

    @app.route("/expense/new", methods=["GET", "POST"])
    @login_required
    def expense_new():
        if request.method == "POST":
            shift_id = request.form.get("shift_id") or None
            trip_id = request.form.get("trip_id") or None
            exp_date = request.form.get("exp_date") or date.today().isoformat()
            category = request.form.get("category") or "General"
            amount = float(request.form.get("amount") or 0)
            notes = request.form.get("notes") or None
            e = Expense(shift_id=int(shift_id) if shift_id else None,
                        trip_id=int(trip_id) if trip_id else None,
                        exp_date=exp_date, category=category, amount=amount, notes=notes)
            db.session.add(e)
            db.session.commit()
            return redirect(url_for("dashboard"))
        shifts = db.session.query(Shift).order_by(Shift.date.desc()).all()
        trips = db.session.query(Trip).order_by(Trip.id.desc()).all()
        return render_template("expenses_form.html", shifts=shifts, trips=trips)

    @app.get("/health")
    def health():
        return {"ok": True, "db_file": db_file, "version": "v13.5.1"}

    return app
