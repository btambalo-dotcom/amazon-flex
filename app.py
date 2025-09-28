
import os
from datetime import datetime, date, time
from io import BytesIO
from flask import Flask, render_template, request, redirect, url_for, flash, Response, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# --- setup
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "login"

def instance_path():
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance")
    os.makedirs(base, exist_ok=True)
    os.makedirs(os.path.join(base, "uploads"), exist_ok=True)
    return base

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "devkey")

    # DB URI: prefer explicit SQLALCHEMY_DATABASE_URI, else DB_FILE under instance/
    uri = os.environ.get("SQLALCHEMY_DATABASE_URI")
    if not uri:
        db_filename = os.environ.get("DB_FILE", "flex.db")
        uri = "sqlite:///" + os.path.join(instance_path(), db_filename)
    app.config["SQLALCHEMY_DATABASE_URI"] = uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(uid):
        return db.session.get(User, int(uid))

    register_routes(app)
    return app

# --- models
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, pw): self.password_hash = generate_password_hash(pw)
    def check_password(self, pw): return check_password_hash(self.password_hash, pw)

class Shift(db.Model):
    __tablename__ = "shifts"
    id = db.Column(db.Integer, primary_key=True)
    work_date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    manual_hours = db.Column(db.Float)  # se quiser digitar as horas manualmente
    notes = db.Column(db.String(500))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    trips = db.relationship("Trip", backref="shift", cascade="all, delete-orphan")
    expenses = db.relationship("Expense", backref="shift", cascade="all, delete-orphan")

    def hours(self):
        if self.manual_hours: return self.manual_hours
        if self.start_time and self.end_time:
            d1 = datetime.combine(self.work_date, self.start_time)
            d2 = datetime.combine(self.work_date, self.end_time)
            return max(0, (d2 - d1).total_seconds()/3600.0)
        return 0.0
    def total_earnings(self): return sum((t.block_pay or 0) + (t.tips or 0) for t in self.trips)
    def total_fuel(self): return sum(t.fuel_cost or 0 for t in self.trips)
    def total_miles(self):
        miles = 0.0
        for t in self.trips:
            if t.odometer_start is not None and t.odometer_end is not None:
                miles += max(0, (t.odometer_end - t.odometer_start))
        return miles
    def other_expenses(self): return sum(e.amount for e in self.expenses)
    def net_profit(self): return self.total_earnings() - self.total_fuel() - self.other_expenses()

class Trip(db.Model):
    __tablename__ = "trips"
    id = db.Column(db.Integer, primary_key=True)
    shift_id = db.Column(db.Integer, db.ForeignKey('shifts.id'), nullable=False, index=True)
    block_pay = db.Column(db.Float, nullable=False, default=0)
    tips = db.Column(db.Float, default=0)
    fuel_cost = db.Column(db.Float)
    fuel_volume_gal = db.Column(db.Float)
    odometer_start = db.Column(db.Integer)
    odometer_end = db.Column(db.Integer)
    notes = db.Column(db.String(500))

class Expense(db.Model):
    __tablename__ = "expenses"
    id = db.Column(db.Integer, primary_key=True)
    shift_id = db.Column(db.Integer, db.ForeignKey('shifts.id'))
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'))
    exp_date = db.Column(db.Date, nullable=False, index=True)
    category = db.Column(db.String(80), nullable=False)
    amount = db.Column(db.Float, nullable=False, default=0.0)
    notes = db.Column(db.String(500))

class ScheduledRide(db.Model):
    __tablename__ = "scheduled_rides"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    start_dt = db.Column(db.DateTime, nullable=False, index=True)
    end_dt = db.Column(db.DateTime)
    expected_block_pay = db.Column(db.Float)
    notes = db.Column(db.String(500))

# --- utils
def _to_date(s):
    try: 
        return datetime.strptime(s, "%Y-%m-%d").date()
    except: 
        return None

def _to_time(s):
    try:
        return datetime.strptime(s, "%H:%M").time()
    except:
        return None

def register_routes(app: Flask):
    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        return render_template("index.html")

    @app.route("/register", methods=["GET","POST"])
    def register():
        if request.method == "POST":
            email = (request.form.get("email") or "").strip().lower()
            pw = request.form.get("password") or ""
            if not email or not pw:
                flash("Preencha email e senha", "warning"); return redirect(url_for("register"))
            if User.query.filter_by(email=email).first():
                flash("Email já registrado", "danger"); return redirect(url_for("login"))
            u = User(email=email); u.set_password(pw); db.session.add(u); db.session.commit()
            flash("Conta criada! Faça login.", "success"); return redirect(url_for("login"))
        return render_template("register.html")

    @app.route("/login", methods=["GET","POST"])
    def login():
        if request.method == "POST":
            email = (request.form.get("email") or "").strip().lower()
            pw = request.form.get("password") or ""
            u = User.query.filter_by(email=email).first()
            if not u or not u.check_password(pw):
                flash("Credenciais inválidas", "danger"); return redirect(url_for("login"))
            login_user(u); return redirect(url_for("dashboard"))
        return render_template("login.html")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user(); return redirect(url_for("login"))

    @app.route("/dashboard")
    @login_required
    def dashboard():
        shifts = Shift.query.order_by(Shift.work_date.desc()).limit(15).all()
        return render_template("dashboard.html", shifts=shifts)

    @app.route("/shift/new", methods=["GET","POST"])
    @login_required
    def shift_new():
        if request.method == "POST":
            s = Shift(
                work_date = _to_date(request.form.get("work_date")) or date.today(),
                start_time = _to_time(request.form.get("start_time")),
                end_time   = _to_time(request.form.get("end_time")),
                manual_hours = float(request.form.get("manual_hours") or 0) or None,
                notes = request.form.get("notes") or None,
                user_id = current_user.id
            )
            db.session.add(s); db.session.commit()
            flash("Turno salvo!", "success"); return redirect(url_for("dashboard"))
        return render_template("shift_form.html")

    @app.route("/trip/new", methods=["GET","POST"])
    @login_required
    def trip_new():
        if request.method == "POST":
            t = Trip(
                shift_id = int(request.form.get("shift_id")),
                block_pay = float(request.form.get("block_pay") or 0),
                tips = float(request.form.get("tips") or 0),
                fuel_cost = float(request.form.get("fuel_cost") or 0) or None,
                fuel_volume_gal = float(request.form.get("fuel_volume_gal") or 0) or None,
                odometer_start = int(request.form.get("odometer_start") or 0) or None,
                odometer_end = int(request.form.get("odometer_end") or 0) or None,
                notes = request.form.get("notes") or None
            )
            db.session.add(t); db.session.commit()
            flash("Corrida salva!", "success"); return redirect(url_for("dashboard"))
        shifts = Shift.query.order_by(Shift.work_date.desc()).all()
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
                exp_date = _to_date(request.form.get("exp_date")) or date.today(),
                category = (request.form.get("category") or "Outros").strip(),
                amount = float(request.form.get("amount") or 0),
                notes = request.form.get("notes") or None,
                shift_id = int(request.form.get("shift_id")) if request.form.get("shift_id") else None,
                trip_id = int(request.form.get("trip_id")) if request.form.get("trip_id") else None
            )
            db.session.add(e); db.session.commit()
            flash("Despesa adicionada!", "success"); return redirect(url_for("expenses_list"))
        shifts = Shift.query.order_by(Shift.work_date.desc()).all()
        return render_template("expenses_form.html", shifts=shifts)

    @app.route("/calendar", methods=["GET","POST"])
    @login_required
    def calendar():
        if request.method == "POST":
            title = request.form.get("title") or "Corrida"
            start_dt = request.form.get("start_dt")
            end_dt = request.form.get("end_dt") or None
            sdt = datetime.fromisoformat(start_dt)
            edt = datetime.fromisoformat(end_dt) if end_dt else None
            r = ScheduledRide(title=title, start_dt=sdt, end_dt=edt,
                              expected_block_pay=float(request.form.get("expected_block_pay") or 0),
                              notes=request.form.get("notes") or None)
            db.session.add(r); db.session.commit()
            flash("Agendado!", "success"); return redirect(url_for("calendar"))
        items = ScheduledRide.query.order_by(ScheduledRide.start_dt.asc()).all()
        return render_template("calendar.html", items=items)

    @app.route("/reports")
    @login_required
    def reports():
        start = _to_date(request.args.get("start") or "")
        end = _to_date(request.args.get("end") or "")
        q = Shift.query
        if start: q = q.filter(Shift.work_date >= start)
        if end: q = q.filter(Shift.work_date <= end)
        shifts = q.order_by(Shift.work_date.asc()).all()
        totals = {
            "earnings": sum(s.total_earnings() for s in shifts),
            "fuel": sum(s.total_fuel() for s in shifts),
            "other": sum(s.other_expenses() for s in shifts),
            "hours": sum(s.hours() for s in shifts),
            "miles": sum(s.total_miles() for s in shifts),
            "days": len(shifts)
        }
        totals["net"] = totals["earnings"] - totals["fuel"] - totals["other"]
        return render_template("reports.html", shifts=shifts, totals=totals, start=start, end=end)

    @app.route("/reports.csv")
    @login_required
    def reports_csv():
        start = _to_date(request.args.get("start") or "")
        end = _to_date(request.args.get("end") or "")
        q = Shift.query
        if start: q = q.filter(Shift.work_date >= start)
        if end: q = q.filter(Shift.work_date <= end)
        shifts = q.order_by(Shift.work_date.asc()).all()
        out = ["date,hours,earnings,fuel,other,net"]
        for s in shifts:
            out.append(f"{s.work_date},{s.hours():.2f},{s.total_earnings():.2f},{s.total_fuel():.2f},{s.other_expenses():.2f},{s.net_profit():.2f}")
        return Response("\n".join(out), mimetype="text/csv",
                        headers={'Content-Disposition': 'attachment; filename=relatorio.csv'})

    @app.route("/reports.pdf")
    @login_required
    def reports_pdf():
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import cm
        start = _to_date(request.args.get("start") or "")
        end = _to_date(request.args.get("end") or "")
        q = Shift.query
        if start: q = q.filter(Shift.work_date >= start)
        if end: q = q.filter(Shift.work_date <= end)
        shifts = q.order_by(Shift.work_date.asc()).all()

        totals = {
            "earnings": sum(s.total_earnings() for s in shifts),
            "fuel": sum(s.total_fuel() for s in shifts),
            "other": sum(s.other_expenses() for s in shifts),
            "hours": sum(s.hours() for s in shifts),
            "miles": sum(s.total_miles() for s in shifts),
            "days": len(shifts)
        }
        totals["net"] = totals["earnings"] - totals["fuel"] - totals["other"]

        buf = BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        W, H = A4
        y = H - 2*cm
        c.setFont("Helvetica-Bold", 14); c.drawString(2*cm, y, "Relatório Amazon Flex"); y -= 0.8*cm
        c.setFont("Helvetica", 10)
        def fmt(d): return d.strftime("%d/%m/%Y") if d else "—"
        c.drawString(2*cm, y, f"Período: {fmt(start)} — {fmt(end)}"); y -= 0.8*cm
        c.setFont("Helvetica-Bold", 11)
        c.drawString(2*cm, y, f"Ganho: ${totals['earnings']:.2f} | Comb.: ${totals['fuel']:.2f} | Outras: ${totals['other']:.2f} | Líquido: ${totals['net']:.2f}"); y -= 0.8*cm
        c.setFont("Helvetica-Bold", 10)
        c.drawString(2*cm, y, "Data"); c.drawString(6*cm, y, "Horas"); c.drawString(8*cm, y, "Corridas"); c.drawString(11*cm, y, "Ganhos"); c.drawString(14*cm, y, "Comb."); c.drawString(16*cm, y, "Líquido"); y -= 0.5*cm
        c.setFont("Helvetica", 9)
        for s in shifts:
            if y < 2*cm: c.showPage(); y = H - 2*cm; c.setFont("Helvetica", 9)
            c.drawString(2*cm, y, s.work_date.strftime("%d/%m/%Y"))
            c.drawRightString(7.3*cm, y, f"{s.hours():.1f}")
            c.drawRightString(9.5*cm, y, f"{len(s.trips)}")
            c.drawRightString(12.8*cm, y, f"${s.total_earnings():.2f}")
            c.drawRightString(15.2*cm, y, f"${s.total_fuel():.2f}")
            c.drawRightString(19.0*cm, y, f"${s.net_profit():.2f}")
            y -= 0.4*cm
        c.showPage(); c.save(); buf.seek(0)
        return Response(buf.read(), mimetype="application/pdf",
                        headers={'Content-Disposition':'attachment; filename=relatorio_flex.pdf'})
