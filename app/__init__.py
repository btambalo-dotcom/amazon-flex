import os
from datetime import datetime, date
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from dateutil import parser as dtparser

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "login"

def instance_path():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "instance")
    os.makedirs(p, exist_ok=True)
    return p

def db_uri():
    uri = os.environ.get("SQLALCHEMY_DATABASE_URI")
    if uri: return uri
    fname = os.environ.get("DB_FILE", "flex_v14.db")
    return "sqlite:///" + os.path.join(instance_path(), fname)

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "devkey")
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        db.create_all()
        # bootstrap admin if none
        if not User.query.first():
            admin_user = os.environ.get("ADMIN_USER", "admin")
            admin_pass = os.environ.get("ADMIN_PASS", "admin123")
            u = User(username=admin_user, is_admin=True)
            u.set_password(admin_pass)
            db.session.add(u); db.session.commit()

    @login_manager.user_loader
    def load_user(uid): return db.session.get(User, int(uid))

    @app.errorhandler(404)
    def nf(e): return render_template("errors/404.html"), 404
    @app.errorhandler(500)
    def ie(e): return render_template("errors/500.html"), 500

    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        return render_template("index.html")

    # ---------- AUTH (username) ----------
    @app.route("/login", methods=["GET","POST"])
    def login():
        if request.method == "POST":
            username = (request.form.get("username") or "").strip()
            pw = request.form.get("password") or ""
            u = User.query.filter_by(username=username).first()
            if not u or not u.check_password(pw):
                flash("Usuário ou senha inválidos.", "danger")
                return redirect(url_for("login"))
            login_user(u); return redirect(url_for("dashboard"))
        return render_template("auth/login.html")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user(); return redirect(url_for("login"))

    # ---------- ADMIN ----------
    def require_admin():
        if not (current_user.is_authenticated and current_user.is_admin):
            abort(403)

    @app.route("/admin/users")
    @login_required
    def admin_users():
        require_admin()
        users = User.query.order_by(User.username.asc()).all()
        return render_template("admin/users.html", users=users)

    @app.route("/admin/users/new", methods=["GET","POST"])
    @login_required
    def admin_users_new():
        require_admin()
        if request.method == "POST":
            username = (request.form.get("username") or "").strip()
            password = request.form.get("password") or ""
            is_admin = True if request.form.get("is_admin")=="on" else False
            if not username or not password:
                flash("Preencha usuário e senha.", "warning")
                return redirect(url_for("admin_users_new"))
            if User.query.filter_by(username=username).first():
                flash("Usuário já existe.", "danger")
                return redirect(url_for("admin_users_new"))
            u = User(username=username, is_admin=is_admin)
            u.set_password(password)
            db.session.add(u); db.session.commit()
            flash("Usuário criado.", "success")
            return redirect(url_for("admin_users"))
        return render_template("admin/new_user.html")

    # ---------- APP PAGES ----------
    @app.route("/dashboard")
    @login_required
    def dashboard():
        shifts = Shift.query.order_by(Shift.work_date.desc()).limit(6).all()
        rides = ScheduledRide.query.order_by(ScheduledRide.start_dt.asc()).limit(6).all()
        return render_template("dashboard.html", shifts=shifts, rides=rides)

    @app.route("/shifts/new", methods=["GET","POST"])
    @login_required
    def shifts_new():
        if request.method == "POST":
            d = parse_date(request.form.get("work_date")) or date.today()
            notes = request.form.get("notes") or None
            s = Shift(work_date=d, notes=notes)
            db.session.add(s); db.session.commit()
            flash("Turno salvo.", "success")
            return redirect(url_for("dashboard"))
        return render_template("shift_form.html")

    @app.route("/trips/new", methods=["GET","POST"])
    @login_required
    def trips_new():
        shifts = Shift.query.order_by(Shift.work_date.desc()).all()
        if request.method == "POST":
            t = Trip(
                shift_id=int(request.form.get("shift_id")),
                block_pay=parse_float(request.form.get("block_pay")) or 0,
                tips=parse_float(request.form.get("tips")) or 0,
                fuel_cost=parse_float(request.form.get("fuel_cost")),
                odometer_start=parse_float(request.form.get("odometer_start")),
                odometer_end=parse_float(request.form.get("odometer_end")),
            )
            db.session.add(t); db.session.commit()
            flash("Corrida registrada.", "success")
            return redirect(url_for("dashboard"))
        return render_template("trip_form.html", shifts=shifts)

    @app.route("/expenses", methods=["GET","POST"])
    @login_required
    def expenses():
        if request.method == "POST":
            e = Expense(
                exp_date=parse_date(request.form.get("exp_date")) or date.today(),
                category=request.form.get("category") or "Outros",
                amount=parse_float(request.form.get("amount")) or 0.0,
                notes=request.form.get("notes") or None
            )
            db.session.add(e); db.session.commit()
            flash("Despesa salva.", "success")
            return redirect(url_for("expenses"))
        items = Expense.query.order_by(Expense.exp_date.desc()).all()
        return render_template("expenses.html", items=items)

    @app.route("/calendar", methods=["GET","POST"])
    @login_required
    def calendar():
        if request.method == "POST":
            r = ScheduledRide(
                title=(request.form.get("title") or "").strip(),
                start_dt=parse_dt(request.form.get("start_dt")) or datetime.utcnow()
            )
            db.session.add(r); db.session.commit()
            flash("Agendado.", "success")
            return redirect(url_for("calendar"))
        rides = ScheduledRide.query.order_by(ScheduledRide.start_dt.asc()).all()
        return render_template("calendar.html", rides=rides)

    # helpers
    def parse_date(s):
        try: return dtparser.parse(s).date()
        except: return None
    def parse_dt(s):
        try: return dtparser.parse(s)
        except: return None
    def parse_float(s):
        try: return float(s)
        except: return None

    return app

# ---------- MODELS (explicit tablenames to fix FKs) ----------
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    def set_password(self, pw): self.password_hash = generate_password_hash(pw)
    def check_password(self, pw): return check_password_hash(self.password_hash, pw)

class Shift(db.Model):
    __tablename__ = "shifts"
    id = db.Column(db.Integer, primary_key=True)
    work_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.String(500))

class Trip(db.Model):
    __tablename__ = "trips"
    id = db.Column(db.Integer, primary_key=True)
    shift_id = db.Column(db.Integer, db.ForeignKey("shifts.id"), nullable=False)
    block_pay = db.Column(db.Float, default=0, nullable=False)
    tips = db.Column(db.Float, default=0)
    fuel_cost = db.Column(db.Float)
    odometer_start = db.Column(db.Float)
    odometer_end = db.Column(db.Float)

class Expense(db.Model):
    __tablename__ = "expenses"
    id = db.Column(db.Integer, primary_key=True)
    exp_date = db.Column(db.Date, nullable=False)
    category = db.Column(db.String(80), nullable=False)
    amount = db.Column(db.Float, default=0.0, nullable=False)
    notes = db.Column(db.String(500))

class ScheduledRide(db.Model):
    __tablename__ = "scheduled_rides"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    start_dt = db.Column(db.DateTime, nullable=False)
