
import os
from datetime import datetime, date, time
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, Response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from dateutil import parser as dtparser

def instance_path():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance")
    os.makedirs(p, exist_ok=True)
    up = os.path.join(p, "uploads")
    os.makedirs(up, exist_ok=True)
    return p

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'devkey')
    db_filename = os.environ.get('DB_FILE', 'flex.db')
    db_path = os.path.join(instance_path(), db_filename)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    return init_app(app)

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "login"

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
    manual_hours = db.Column(db.Float)
    notes = db.Column(db.String(500))
    trips = db.relationship("Trip", backref="shift", cascade="all, delete-orphan")

    def hours(self):
        if self.manual_hours: return self.manual_hours
        if self.start_time and self.end_time:
            dt1 = datetime.combine(self.work_date, self.start_time)
            dt2 = datetime.combine(self.work_date, self.end_time)
            return (dt2 - dt1).total_seconds()/3600.0
        return 0.0
    def total_earnings(self): return sum(t.block_pay + (t.tips or 0) for t in self.trips)
    def total_fuel(self): return sum(t.fuel_cost or 0 for t in self.trips)
    def total_miles(self):
        miles = 0.0
        for t in self.trips:
            if t.odometer_start is not None and t.odometer_end is not None:
                miles += max(0, t.odometer_end - t.odometer_start)
        return miles
    def net_profit(self):
        extra = sum(e.amount for e in Expense.query.filter(Expense.shift_id==self.id).all())
        return self.total_earnings() - self.total_fuel() - extra

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
    receipt_path = db.Column(db.String(300))
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

def init_app(app):
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(uid): return db.session.get(User, int(uid))

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/register", methods=["GET","POST"])
    def register():
        if request.method == "POST":
            email = (request.form.get("email") or "").strip().lower()
            pw = request.form.get("password") or ""
            if not email or not pw:
                flash("Preencha email e senha.", "warning")
                return redirect(url_for("register"))
            if User.query.filter_by(email=email).first():
                flash("Email já registrado.", "danger"); return redirect(url_for("register"))
            u = User(email=email); u.set_password(pw); db.session.add(u); db.session.commit()
            flash("Conta criada!", "success"); return redirect(url_for("login"))
        return render_template("register.html")

    @app.route("/login", methods=["GET","POST"])
    def login():
        if request.method == "POST":
            email = (request.form.get("email") or "").strip().lower()
            pw = request.form.get("password") or ""
            u = User.query.filter_by(email=email).first()
            if not u or not u.check_password(pw):
                flash("Credenciais inválidas.", "danger"); return redirect(url_for("login"))
            login_user(u); return redirect(url_for("dashboard"))
        return render_template("login.html")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user(); return redirect(url_for("login"))

    @app.route("/dashboard")
    @login_required
    def dashboard():
        shifts = Shift.query.order_by(Shift.work_date.desc()).limit(10).all()
        return render_template("dashboard.html", shifts=shifts)

    # Expenses
    def parse_date(s):
        try: return dtparser.parse(s).date()
        except: return None

    def parse_float(s):
        try: return float(s)
        except: return None

    @app.route("/expenses")
    @login_required
    def expenses_list():
        items = Expense.query.order_by(Expense.exp_date.desc()).all()
        return render_template("expenses_list.html", items=items)

    @app.route("/expenses/new", methods=["GET","POST"])
    @login_required
    def expenses_new():
        if request.method == "POST":
            ex = Expense(
                exp_date = parse_date(request.form.get("exp_date")) or date.today(),
                category = (request.form.get("category") or "Outros").strip(),
                amount = parse_float(request.form.get("amount") or "0") or 0.0,
                notes = request.form.get("notes") or None,
                shift_id = int(request.form.get("shift_id")) if request.form.get("shift_id") else None
            )
            db.session.add(ex); db.session.commit()
            flash("Despesa registrada!", "success")
            return redirect(url_for("expenses_list"))
        shifts = Shift.query.order_by(Shift.work_date.desc()).all()
        return render_template("expenses_form.html", expense=None, shifts=shifts)

    # Reports PDF
    @app.route("/reports/pdf")
    @login_required
    def reports_pdf():
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import cm
        start = parse_date(request.args.get('start') or '')
        end = parse_date(request.args.get('end') or '')
        q = Shift.query
        if start: q = q.filter(Shift.work_date >= start)
        if end: q = q.filter(Shift.work_date <= end)
        shifts = q.order_by(Shift.work_date.asc()).all()

        extra_total = 0.0
        for s in shifts:
            extra_total += sum(e.amount for e in Expense.query.filter(Expense.shift_id==s.id).all())

        totals = {
            'earnings': sum(s.total_earnings() for s in shifts),
            'fuel': sum(s.total_fuel() for s in shifts),
            'extra': extra_total,
            'miles': sum(s.total_miles() for s in shifts),
            'hours': sum(s.hours() for s in shifts),
            'days': len(shifts)
        }
        totals['net'] = totals['earnings'] - totals['fuel'] - totals['extra']

        import io
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        W,H = A4
        y = H - 2*cm
        c.setFont("Helvetica-Bold", 14); c.drawString(2*cm, y, "Relatório Amazon Flex"); y -= 0.8*cm
        c.setFont("Helvetica", 11)
        def fmt(d): return d.strftime('%d/%m/%Y') if d else '—'
        c.drawString(2*cm, y, f"Período: {fmt(start)} — {fmt(end)}"); y -= 1.0*cm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2*cm, y, f"Ganho: ${totals['earnings']:.2f} | Comb.: ${totals['fuel']:.2f} | Outras: ${totals['extra']:.2f} | Líquido: ${totals['net']:.2f}"); y -= 1.0*cm
        c.setFont("Helvetica", 10)
        c.drawString(2*cm, y, f"Horas: {totals['hours']:.1f} | Milhas: {totals['miles']:.1f} | Dias: {totals['days']}"); y -= 1.0*cm
        c.setFont("Helvetica-Bold", 10)
        c.drawString(2*cm, y, "Data"); c.drawString(6*cm, y, "Horas"); c.drawString(8*cm, y, "Corridas"); c.drawString(11*cm, y, "Ganhos"); c.drawString(14*cm, y, "Comb."); c.drawString(16*cm, y, "Líquido"); y -= 0.6*cm
        c.setFont("Helvetica", 10)
        for s in shifts:
            if y < 2*cm: c.showPage(); y = H - 2*cm
            extra = sum(e.amount for e in Expense.query.filter(Expense.shift_id==s.id).all())
            net = s.total_earnings() - s.total_fuel() - extra
            c.drawString(2*cm, y, s.work_date.strftime('%d/%m/%Y'))
            c.drawRightString(7.3*cm, y, f"{s.hours():.1f}")
            c.drawRightString(9.5*cm, y, f"{len(s.trips)}")
            c.drawRightString(12.8*cm, y, f"${s.total_earnings():.2f}")
            c.drawRightString(15.2*cm, y, f"${s.total_fuel():.2f}")
            c.drawRightString(19.0*cm, y, f"${net:.2f}")
            y -= 0.5*cm
        c.showPage(); c.save(); buf.seek(0)
        return Response(buf.read(), mimetype='application/pdf', headers={'Content-Disposition':'attachment; filename=relatorio_flex.pdf'})

    return app

# expose factory for gunicorn
def create_app():  # noqa - for gunicorn string target
    return init_app(Flask(__name__))
