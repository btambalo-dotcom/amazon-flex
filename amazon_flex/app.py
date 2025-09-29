import os
from datetime import date, datetime
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, send_file
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import text
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from .extensions import db, login_manager
from .models import User, Shift, Trip, Expense, ScheduledRide

def _ensure_schema(app):
    with app.app_context():
        db.create_all()

        def cols(table):
            rows = db.session.execute(text(f"PRAGMA table_info({table});")).mappings().all()
            return {r['name']: r for r in rows}

        expected = {
            'users': {'id':'INTEGER','email':'VARCHAR(120)','password_hash':'VARCHAR(255)','created_at':'DATETIME'},
            'shifts': {'id':'INTEGER','date':'DATE','hours_worked':'FLOAT','created_at':'DATETIME'},
            'trips': {'id':'INTEGER','shift_id':'INTEGER','fare_amount':'FLOAT','fuel_cost':'FLOAT','odometer':'FLOAT','tips':'FLOAT','created_at':'DATETIME'},
            'expenses': {'id':'INTEGER','shift_id':'INTEGER','trip_id':'INTEGER','exp_date':'DATE','category':'VARCHAR(100)','amount':'FLOAT','notes':'VARCHAR(500)','created_at':'DATETIME'},
            'scheduled_rides': {
                'id':'INTEGER','title':'VARCHAR(120)','start_dt':'DATETIME','end_dt':'DATETIME',
                'hours_planned':'FLOAT','expected_block_pay':'FLOAT','tips':'FLOAT','fuel_cost':'FLOAT',
                'odometer_start':'FLOAT','odometer_end':'FLOAT','notes':'VARCHAR(500)','created_at':'DATETIME'
            },
        }
        for table, cmap in expected.items():
            try:
                existing = cols(table)
            except Exception:
                existing = {}
            for name, sqltype in cmap.items():
                if name not in existing:
                    db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {sqltype};"))
        db.session.commit()

def _seed_admin():
    email = os.getenv("ADMIN_EMAIL")
    password = os.getenv("ADMIN_PASSWORD")
    if not email or not password:
        return
    if not db.session.query(User).filter_by(email=email.lower()).first():
        u = User(email=email.lower())
        u.set_password(password)
        db.session.add(u)
        db.session.commit()

def create_app():
    app = Flask(__name__)

    instance_dir = os.path.join(os.getcwd(), "instance")
    os.makedirs(instance_dir, exist_ok=True)

    secret = os.getenv("SECRET_KEY", "mude-esta-chave")
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

    with app.app_context():
        _ensure_schema(app)
        _seed_admin()

    # ----------- Autenticação -----------
    @app.route("/registrar", methods=["GET", "POST"])
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

    @app.route("/entrar", methods=["GET", "POST"])
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

    @app.get("/sair")
    @login_required
    def sair():
        logout_user()
        return redirect(url_for("index"))

    # ----------- Páginas -----------
    @app.get("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        return render_template("index.html")

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

    # ----------- Forms simples -----------
    @app.route("/shift/nova", methods=["GET", "POST"])
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

    @app.route("/trip/nova", methods=["GET", "POST"])
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

    @app.route("/despesa/nova", methods=["GET", "POST"])
    @login_required
    def expense_new():
        if request.method == "POST":
            shift_id = request.form.get("shift_id") or None
            trip_id = request.form.get("trip_id") or None
            exp_date = request.form.get("exp_date") or date.today().isoformat()
            category = request.form.get("category") or "Geral"
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

    # ----------- Calendário / Agendamentos -----------
    @app.get("/calendario")
    @login_required
    def calendar_view():
        rides = db.session.query(ScheduledRide).order_by(ScheduledRide.start_dt.desc()).limit(8).all()
        return render_template("calendar.html", rides=rides)

    @app.route("/agendamento/novo", methods=["GET", "POST"])
    @login_required
    def scheduled_new():
        if request.method == "POST":
            title = request.form.get("title") or "Corrida Amazon Flex"
            start_dt = datetime.fromisoformat(request.form.get("start_dt"))
            end_raw = request.form.get("end_dt") or None
            end_dt = datetime.fromisoformat(end_raw) if end_raw else None
            hours_planned = request.form.get("hours_planned") or None
            hours_planned = float(hours_planned) if hours_planned else None
            pay = request.form.get("expected_block_pay") or None
            pay = float(pay) if pay else None
            tips = request.form.get("tips") or None
            tips = float(tips) if tips else None
            fuel = request.form.get("fuel_cost") or None
            fuel = float(fuel) if fuel else None
            od_start = request.form.get("odometer_start") or None
            od_end = request.form.get("odometer_end") or None
            od_start = float(od_start) if od_start else None
            od_end = float(od_end) if od_end else None
            notes = request.form.get("notes") or None
            sr = ScheduledRide(title=title, start_dt=start_dt, end_dt=end_dt,
                               hours_planned=hours_planned, expected_block_pay=pay,
                               tips=tips, fuel_cost=fuel, odometer_start=od_start,
                               odometer_end=od_end, notes=notes)
            db.session.add(sr)
            db.session.commit()
            flash("Corrida agendada.", "success")
            return redirect(url_for("calendar_view"))
        return render_template("scheduled_form.html", mode="new")

    @app.route("/agendamento/<int:ride_id>/editar", methods=["GET", "POST"])
    @login_required
    def scheduled_edit(ride_id):
        r = db.session.get(ScheduledRide, ride_id)
        if not r:
            flash("Agendamento não encontrado.", "warning")
            return redirect(url_for("calendar_view"))
        if request.method == "POST":
            r.title = request.form.get("title") or r.title
            r.start_dt = datetime.fromisoformat(request.form.get("start_dt"))
            end_raw = request.form.get("end_dt") or None
            r.end_dt = datetime.fromisoformat(end_raw) if end_raw else None
            r.hours_planned = float(request.form.get("hours_planned") or 0) or None
            r.expected_block_pay = float(request.form.get("expected_block_pay") or 0) or None
            r.tips = float(request.form.get("tips") or 0) or None
            r.fuel_cost = float(request.form.get("fuel_cost") or 0) or None
            od_start = request.form.get("odometer_start") or None
            od_end = request.form.get("odometer_end") or None
            r.odometer_start = float(od_start) if od_start else None
            r.odometer_end = float(od_end) if od_end else None
            r.notes = request.form.get("notes") or None
            db.session.commit()
            flash("Agendamento atualizado.", "success")
            return redirect(url_for("calendar_view"))
        return render_template("scheduled_form.html", mode="edit", ride=r)

    @app.post("/agendamento/<int:ride_id>/excluir")
    @login_required
    def scheduled_delete(ride_id):
        r = db.session.get(ScheduledRide, ride_id)
        if not r:
            flash("Agendamento não encontrado.", "warning")
        else:
            db.session.delete(r)
            db.session.commit()
            flash("Agendamento excluído.", "success")
        return redirect(url_for("calendar_view"))

    @app.get("/api/agendamentos")
    @login_required
    def api_scheduled():
        rides = db.session.query(ScheduledRide).order_by(ScheduledRide.start_dt.asc()).all()
        def event_title(r):
            parts = [r.title or "Corrida"]
            if r.end_dt:
                dur = (r.end_dt - r.start_dt).total_seconds() / 3600.0
            else:
                dur = r.hours_planned
            if dur:
                parts.append(f"{dur:.1f}h")
            if r.expected_block_pay:
                parts.append(f"R$ {r.expected_block_pay:,.2f}".replace(',', 'X').replace('.', ',').replace('X','.'))
            if r.tips:
                parts.append(f"+ gorj R$ {r.tips:,.2f}".replace(',', 'X').replace('.', ',').replace('X','.'))
            return " • ".join(parts)
        return jsonify([{
            "id": r.id,
            "title": event_title(r),
            "start": r.start_dt.isoformat(),
            "end": r.end_dt.isoformat() if r.end_dt else None,
        } for r in rides])

    # ----------- Relatórios + PDF + Líquido -----------
    def _calc_report(inicio, fim):
        items, totais = [], dict(horas=0.0, km=0.0, valor=0.0, tips=0.0, combustivel=0.0, despesas=0.0, qtd=0, liquido=0.0)
        dt_ini = datetime.fromisoformat(inicio)
        dt_fim = datetime.fromisoformat(fim)
        q = db.session.query(ScheduledRide).filter(ScheduledRide.start_dt >= dt_ini, ScheduledRide.start_dt <= dt_fim).order_by(ScheduledRide.start_dt.asc())
        for r in q.all():
            horas = (r.end_dt - r.start_dt).total_seconds() / 3600.0 if r.end_dt else (r.hours_planned or 0.0)
            km = 0.0
            if r.odometer_start is not None and r.odometer_end is not None:
                km = max(0.0, r.odometer_end - r.odometer_start)
            valor = r.expected_block_pay or 0.0
            tips = r.tips or 0.0
            fuel = r.fuel_cost or 0.0
            items.append(dict(
                data=r.start_dt.strftime("%d/%m/%Y %H:%M"),
                horas=horas, km=km, valor=valor, tips=tips, combustivel=fuel,
                titulo=r.title or "Corrida", notas=r.notes or ""
            ))
            totais["horas"] += horas
            totais["km"] += km
            totais["valor"] += valor
            totais["tips"] += tips
            totais["combustivel"] += fuel
            totais["qtd"] += 1
        # Despesas gerais (fora combustível já informado nas corridas)
        exp_q = db.session.query(Expense).filter(Expense.exp_date >= dt_ini.date(), Expense.exp_date <= dt_fim.date())
        despesas = sum((e.amount or 0.0) for e in exp_q.all())
        totais["despesas"] = despesas
        totais["liquido"] = (totais["valor"] + totais["tips"]) - (totais["combustivel"] + totais["despesas"])
        return items, totais

    @app.route("/relatorios", methods=["GET"])
    @login_required
    def reports():
        inicio = request.values.get("inicio")
        fim = request.values.get("fim")
        items, totais = [], dict(horas=0.0, km=0.0, valor=0.0, tips=0.0, combustivel=0.0, despesas=0.0, qtd=0, liquido=0.0)
        if inicio and fim:
            try:
                items, totais = _calc_report(inicio, fim)
            except ValueError:
                flash("Datas inválidas.", "warning")
        return render_template("reports.html", items=items, totais=totais, inicio=inicio, fim=fim)

    @app.get("/relatorios/pdf")
    @login_required
    def reports_pdf():
        inicio = request.args.get("inicio")
        fim = request.args.get("fim")
        if not (inicio and fim):
            flash("Informe as datas para exportar o PDF.", "warning")
            return redirect(url_for("reports"))
        items, totais = _calc_report(inicio, fim)

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        y = height - 50
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, y, f"Relatório de {inicio} a {fim}")
        y -= 20
        c.setFont("Helvetica", 10)
        for it in items:
            line = f"{it['data']} | {it['titulo']} | Hrs {it['horas']:.1f} | KM {it['km']:.1f} | R$ {it['valor']:.2f} | Gorj {it['tips']:.2f} | Comb {it['combustivel']:.2f}"
            if y < 80:
                c.showPage(); y = height - 50; c.setFont("Helvetica", 10)
            c.drawString(40, y, line); y -= 14
        y -= 10
        c.setFont("Helvetica-Bold", 11)
        c.drawString(40, y, f"Totais: Hrs {totais['horas']:.1f} | KM {totais['km']:.1f} | Valor R$ {totais['valor']:.2f} | Gorj R$ {totais['tips']:.2f} | Comb R$ {totais['combustivel']:.2f} | Despesas R$ {totais['despesas']:.2f} | Líquido R$ {totais['liquido']:.2f}")
        c.showPage()
        c.save()
        buffer.seek(0)
        filename = f"relatorio_{inicio}_a_{fim}.pdf"
        return send_file(buffer, as_attachment=True, download_name=filename, mimetype="application/pdf")

    @app.get("/saude")
    def health():
        return {"ok": True, "version": "v14.4"}

    return app
