import os, io
from datetime import datetime, date
from flask import Flask, render_template, request, redirect, url_for, flash, Response, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import inspect
from dateutil import parser as dtparser

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "login"

def _instance_path():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "instance")
    os.makedirs(p, exist_ok=True)
    os.makedirs(os.path.join(p, "uploads"), exist_ok=True)
    return p

def _sql_uri():
    uri = os.environ.get("SQLALCHEMY_DATABASE_URI")
    if uri: return uri
    db_filename = os.environ.get("DB_FILE", "flex.db")
    return "sqlite:///" + os.path.join(_instance_path(), db_filename)

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "devkey")
    app.config["SQLALCHEMY_DATABASE_URI"] = _sql_uri()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    migrate.init_app(app, db, directory=os.path.join(os.path.dirname(__file__), "..", "migrations"))
    login_manager.init_app(app)

    # --- Auto-init DB on first request (fallback) ---
    with app.app_context():
        insp = inspect(db.engine)
        if not insp.has_table("users"):
            db.create_all()

    @login_manager.user_loader
    def load_user(uid): return db.session.get(User, int(uid))

    @app.errorhandler(404)
    def not_found(e): return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal(e): return render_template("errors/500.html"), 500

    @app.route("/health")
    def health(): return {"ok": True}, 200

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(app.static_folder, 'favicon.ico', mimetype='image/vnd.microsoft.icon')

    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        return render_template("index.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            email = (request.form.get("email") or "").strip().lower()
            pw = request.form.get("password") or ""
            if not email or not pw:
                flash("Preencha email e senha.", "warning")
                return redirect(url_for("register"))
            if User.query.filter_by(email=email).first():
                flash("Email já registrado.", "danger")
                return redirect(url_for("register"))
            u = User(email=email); u.set_password(pw)
            db.session.add(u); db.session.commit()
            flash("Conta criada! Faça login.", "success")
            return redirect(url_for("login"))
        return render_template("auth/register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = (request.form.get("email") or "").strip().lower()
            pw = request.form.get("password") or ""
            u = User.query.filter_by(email=email).first()
            if not u or not u.check_password(pw):
                flash("Credenciais inválidas.", "danger")
                return redirect(url_for("login"))
            login_user(u); return redirect(url_for("dashboard"))
        return render_template("auth/login.html")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user(); return redirect(url_for("login"))

    @app.route("/dashboard")
    @login_required
    def dashboard():
        shifts = Shift.query.order_by(Shift.work_date.desc()).limit(6).all()
        rides = ScheduledRide.query.order_by(ScheduledRide.start_dt.asc()).limit(6).all()
        return render_template("dashboard.html", shifts=shifts, rides=rides)

    # Forms simplified (same as v12)
    @app.route("/shifts/new", methods=["GET","POST"])
    @login_required
    def shifts_new():
        if request.method == "POST":
            s = Shift(
                work_date=_parse_date(request.form.get("work_date")) or date.today(),
                notes=request.form.get("notes") or None
            )
            db.session.add(s); db.session.commit()
            flash("Turno adicionado.", "success")
            return redirect(url_for("dashboard"))
        return render_template("shift_form.html")

    @app.route("/trips/new", methods=["GET","POST"])
    @login_required
    def trips_new():
        shifts = Shift.query.order_by(Shift.work_date.desc()).all()
        if request.method == "POST":
            t = Trip(
                shift_id=int(request.form.get("shift_id")),
                block_pay=_parse_float(request.form.get("block_pay")) or 0,
                tips=_parse_float(request.form.get("tips")) or 0,
                fuel_cost=_parse_float(request.form.get("fuel_cost")),
                odometer_start=_parse_float(request.form.get("odometer_start")),
                odometer_end=_parse_float(request.form.get("odometer_end"))
            )
            db.session.add(t); db.session.commit()
            flash("Corrida registrada.", "success")
            return redirect(url_for("dashboard"))
        return render_template("trip_form.html", shifts=shifts)

    @app.route("/expenses", methods=["GET"])
    @login_required
    def expenses_list():
        items = Expense.query.order_by(Expense.exp_date.desc()).all()
        return render_template("expenses_list.html", items=items)

    @app.route("/expenses/new", methods=["GET","POST"])
    @login_required
    def expenses_new():
        if request.method == "POST":
            e = Expense(
                exp_date=_parse_date(request.form.get("exp_date")) or date.today(),
                category=(request.form.get("category") or "Outros").strip(),
                amount=_parse_float(request.form.get("amount") or "0") or 0.0,
                notes=request.form.get("notes") or None
            )
            db.session.add(e); db.session.commit()
            flash("Despesa adicionada.", "success")
            return redirect(url_for("expenses_list"))
        return render_template("expenses_form.html")

    @app.route("/calendar")
    @login_required
    def calendar():
        rides = ScheduledRide.query.order_by(ScheduledRide.start_dt.asc()).all()
        return render_template("calendar.html", rides=rides)

    @app.route("/calendar/new", methods=["GET","POST"])
    @login_required
    def calendar_new():
        if request.method == "POST":
            r = ScheduledRide(
                title=(request.form.get("title") or "").strip(),
                start_dt=_parse_dt(request.form.get("start_dt")) or datetime.utcnow()
            )
            db.session.add(r); db.session.commit()
            flash("Corrida agendada.", "success")
            return redirect(url_for("calendar"))
        return render_template("calendar_form.html")

    @app.route("/reports/pdf")
    @login_required
    def reports_pdf():
        # Minimal placeholder
        return Response(b'%PDF-1.4\n% v13 placeholder\n', mimetype="application/pdf",
                        headers={'Content-Disposition': 'attachment; filename=relatorio.pdf'})

    # Helpers
    def _parse_date(s):
        try: return dtparser.parse(s).date()
        except: return None
    def _parse_dt(s):
        try: return dtparser.parse(s)
        except: return None
    def _parse_float(s):
        try: return float(s)
        except: return None

    return app

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    def set_password(self, pw): self.password_hash = generate_password_hash(pw)
    def check_password(self, pw): return check_password_hash(self.password_hash, pw)

class Shift(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    work_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.String(500))
    trips = db.relationship("Trip", backref="shift", cascade="all, delete-orphan")

class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shift_id = db.Column(db.Integer, db.ForeignKey('shift.id') if False else db.ForeignKey('shift'.replace('shift','shifts')+'.id'), nullable=False)
    block_pay = db.Column(db.Float, nullable=False, default=0)
    tips = db.Column(db.Float, default=0)
    fuel_cost = db.Column(db.Float)
    odometer_start = db.Column(db.Float)
    odometer_end = db.Column(db.Float)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shift_id = db.Column(db.Integer)
    exp_date = db.Column(db.Date, nullable=False)
    category = db.Column(db.String(80), nullable=False)
    amount = db.Column(db.Float, nullable=False, default=0.0)
    notes = db.Column(db.String(500))

class ScheduledRide(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    start_dt = db.Column(db.DateTime, nullable=False)

