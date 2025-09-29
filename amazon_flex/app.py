
import os, secrets, io, csv
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, send_file
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import text
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from openpyxl import Workbook
from .extensions import db, login_manager
from .models import User, Shift, Trip, Expense, ScheduledRide

def _ensure_schema(app):
    with app.app_context():
        db.create_all()
        def cols(t):
            rows = db.session.execute(text(f"PRAGMA table_info({t});")).mappings().all()
            return {r['name'] for r in rows}
        expected = {
            'users': ["id","email","password_hash","created_at"],
            'shifts': ["id","date","hours_worked","created_at"],
            'trips': ["id","shift_id","fare_amount","fuel_cost","odometer","tips","created_at"],
            'expenses': ["id","exp_date","category","amount","notes","created_at"],
            'scheduled_rides': ["id","title","start_dt","end_dt","hours_planned","expected_block_pay","tips","fuel_cost","odometer_start","odometer_end","notes","created_at"]
        }
        type_map = dict(id="INTEGER", email="VARCHAR(120)", password_hash="VARCHAR(255)",
                        created_at="DATETIME", date="DATE", hours_worked="FLOAT",
                        shift_id="INTEGER", fare_amount="FLOAT", fuel_cost="FLOAT",
                        odometer="FLOAT", tips="FLOAT",
                        exp_date="DATE", category="VARCHAR(100)", amount="FLOAT", notes="VARCHAR(500)",
                        title="VARCHAR(120)", start_dt="DATETIME", end_dt="DATETIME",
                        hours_planned="FLOAT", expected_block_pay="FLOAT",
                        odometer_start="FLOAT", odometer_end="FLOAT")
        for table, cols_expected in expected.items():
            existing = cols(table)
            for c in cols_expected:
                if c not in existing:
                    db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {c} {type_map.get(c,'TEXT')};"))
        db.session.commit()

def create_app():
    app = Flask(__name__)
    instance_dir = os.path.join(os.getcwd(), "instance"); os.makedirs(instance_dir, exist_ok=True)
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", secrets.token_hex(16)),
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{os.path.join(instance_dir, os.getenv('DB_FILE','flex.db'))}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    db.init_app(app); login_manager.init_app(app); login_manager.login_view="login"
    @login_manager.user_loader
    def load_user(user_id): return db.session.get(User, int(user_id))
    _ensure_schema(app)

    @app.get("/")
    def index():
        if current_user.is_authenticated: return redirect(url_for("dashboard"))
        return render_template("index.html")

    @app.route("/registrar", methods=["GET","POST"])
    def register():
        if request.method=="POST":
            email=request.form.get("email","").strip().lower(); pwd=request.form.get("password","")
            if not email or not pwd: flash("Informe email e senha.","warning"); return redirect(url_for("register"))
            if db.session.query(User).filter_by(email=email).first(): flash("Email já cadastrado.","danger"); return redirect(url_for("register"))
            u=User(email=email); u.set_password(pwd); db.session.add(u); db.session.commit()
            flash("Conta criada. Faça login.","success"); return redirect(url_for("login"))
        return render_template("register.html")

    @app.route("/entrar", methods=["GET","POST"])
    def login():
        if request.method=="POST":
            email=request.form.get("email","").strip().lower(); pwd=request.form.get("password","")
            u=db.session.query(User).filter_by(email=email).first()
            if u and u.check_password(pwd): login_user(u); return redirect(url_for("dashboard"))
            flash("Credenciais inválidas.","danger")
        return render_template("login.html")

    @app.get("/sair"); @login_required
    def logout(): logout_user(); return redirect(url_for("index"))

    @app.get("/dashboard"); @login_required
    def dashboard():
        f=db.session.query(db.func.coalesce(db.func.sum(Trip.fare_amount),0.0)).scalar()
        t=db.session.query(db.func.coalesce(db.func.sum(Trip.tips),0.0)).scalar()
        fc=db.session.query(db.func.coalesce(db.func.sum(Trip.fuel_cost),0.0)).scalar()
        e=db.session.query(db.func.coalesce(db.func.sum(Expense.amount),0.0)).scalar()
        return render_template("dashboard.html", totals=dict(shifts=db.session.query(Shift).count(), trips=db.session.query(Trip).count(), fare=f, tips=t, fuel=fc, expenses=e))

    # --------- Corridas (CRUD) ---------
    @app.get("/corridas"); @login_required
    def scheduled_list():
        rides=db.session.query(ScheduledRide).order_by(ScheduledRide.start_dt.desc()).all()
        return render_template("scheduled_list.html", rides=rides)

    @app.get("/calendario"); @login_required
    def calendar_view(): return render_template("calendar.html")

    @app.route("/corrida/nova", methods=["GET","POST"]); @login_required
    def scheduled_new():
        if request.method=="POST":
            g=lambda k: request.form.get(k) or None
            r=ScheduledRide(
                title=g("title") or "Corrida Amazon Flex",
                start_dt=datetime.fromisoformat(request.form["start_dt"]),
                end_dt=(datetime.fromisoformat(g("end_dt")) if g("end_dt") else None),
                hours_planned=(float(g("hours_planned")) if g("hours_planned") else None),
                expected_block_pay=(float(g("expected_block_pay")) if g("expected_block_pay") else None),
                tips=(float(g("tips")) if g("tips") else None),
                fuel_cost=(float(g("fuel_cost")) if g("fuel_cost") else None),
                odometer_start=(float(g("odometer_start")) if g("odometer_start") else None),
                odometer_end=(float(g("odometer_end")) if g("odometer_end") else None),
                notes=g("notes")
            ); db.session.add(r); db.session.commit(); flash("Corrida agendada.","success"); return redirect(url_for("calendar_view"))
        return render_template("scheduled_form.html")

    @app.route("/corrida/<int:ride_id>/editar", methods=["GET","POST"]); @login_required
    def scheduled_edit(ride_id):
        r=db.session.get(ScheduledRide, ride_id)
        if not r: flash("Corrida não encontrada.","warning"); return redirect(url_for("scheduled_list"))
        if request.method=="POST":
            g=lambda k: request.form.get(k) or None
            r.title=g("title") or r.title
            r.start_dt=datetime.fromisoformat(request.form["start_dt"])
            r.end_dt=(datetime.fromisoformat(g("end_dt")) if g("end_dt") else None)
            r.hours_planned=(float(g("hours_planned")) if g("hours_planned") else None)
            r.expected_block_pay=(float(g("expected_block_pay")) if g("expected_block_pay") else None)
            r.tips=(float(g("tips")) if g("tips") else None)
            r.fuel_cost=(float(g("fuel_cost")) if g("fuel_cost") else None)
            r.odometer_start=(float(g("odometer_start")) if g("odometer_start") else None)
            r.odometer_end=(float(g("odometer_end")) if g("odometer_end") else None)
            r.notes=g("notes")
            db.session.commit(); flash("Corrida atualizada.","success"); return redirect(url_for("scheduled_list"))
        return render_template("scheduled_edit.html", r=r)

    @app.post("/corrida/<int:ride_id>/excluir"); @login_required
    def scheduled_delete(ride_id):
        r=db.session.get(ScheduledRide, ride_id)
        if not r: flash("Corrida não encontrada.","warning"); return redirect(url_for("scheduled_list"))
        db.session.delete(r); db.session.commit(); flash("Corrida excluída.","success"); return redirect(url_for("scheduled_list"))

    @app.get("/api/agendamentos"); @login_required
    def api_scheduled():
        rides=db.session.query(ScheduledRide).order_by(ScheduledRide.start_dt.asc()).all()
        def title(r):
            parts=[r.title or "Corrida"]
            dur=((r.end_dt - r.start_dt).total_seconds()/3600.0) if r.end_dt else r.hours_planned
            if dur: parts.append(f"{dur:.1f}h")
            if r.expected_block_pay: parts.append(f"R$ {r.expected_block_pay:,.2f}".replace(',', 'X').replace('.', ',').replace('X','.'))
            return " • ".join(parts)
        return jsonify([{"id":r.id,"title":title(r),"start":r.start_dt.isoformat(),"end":(r.end_dt.isoformat() if r.end_dt else None),"url":url_for("scheduled_edit", ride_id=r.id)} for r in rides])

    # --------- Relatórios + PDF/CSV/XLSX ---------
    def _query_report(inicio, fim):
        d_ini=datetime.fromisoformat(inicio+"T00:00:00"); d_fim=datetime.fromisoformat(fim+"T23:59:59")
        q=db.session.query(ScheduledRide).filter(ScheduledRide.start_dt>=d_ini, ScheduledRide.start_dt<=d_fim).order_by(ScheduledRide.start_dt.asc())
        items=[]; tot=dict(horas=0.0,km=0.0,valor=0.0,tips=0.0,combustivel=0.0,qtd=0)
        for r in q.all():
            horas=((r.end_dt - r.start_dt).total_seconds()/3600.0) if r.end_dt else (r.hours_planned or 0.0)
            km=((r.odometer_end or 0)-(r.odometer_start or 0)) if (r.odometer_start is not None and r.odometer_end is not None) else 0.0
            valor=r.expected_block_pay or 0.0; tips=r.tips or 0.0; fuel=r.fuel_cost or 0.0
            items.append(dict(data=r.start_dt.strftime("%d/%m/%Y %H:%M"), horas=horas, km=max(0.0,km), valor=valor, tips=tips, combustivel=fuel, titulo=r.title or "Corrida", notas=r.notes or ""))
            tot["horas"]+=horas; tot["km"]+=max(0.0,km); tot["valor"]+=valor; tot["tips"]+=tips; tot["combustivel"]+=fuel; tot["qtd"]+=1
        return items, tot

    @app.route("/relatorios", methods=["GET","POST"]); @login_required
    def reports():
        inicio=request.values.get("inicio"); fim=request.values.get("fim")
        items=[]; tot=dict(horas=0.0,km=0.0,valor=0.0,tips=0.0,combustivel=0.0,qtd=0)
        if inicio and fim:
            items, tot = _query_report(inicio, fim)
        return render_template("reports.html", items=items, totais=tot, inicio=inicio, fim=fim)

    @app.get("/relatorios/pdf"); @login_required
    def reports_pdf():
        inicio=request.args.get("inicio"); fim=request.args.get("fim")
        if not inicio or not fim: flash("Informe início e fim.","warning"); return redirect(url_for("reports"))
        items, tot = _query_report(inicio, fim)
        # PDF
        buf=io.BytesIO(); c=canvas.Canvas(buf, pagesize=landscape(A4)); W,H=landscape(A4); m=1.2*cm; x=m; y=H-m
        c.setFont("Helvetica-Bold", 14); c.drawString(x,y,f"Relatório — {inicio} a {fim}"); y-=0.8*cm
        c.setFont("Helvetica", 11); c.drawString(x,y,f"Totais: Corridas={tot['qtd']} | Horas={tot['horas']:.1f} | KM={tot['km']:.1f} | Valor=R$ {tot['valor']:.2f} | Gorjetas=R$ {tot['tips']:.2f} | Combustível=R$ {tot['combustivel']:.2f}"); y-=0.6*cm
        headers=["Início","Horas","KM","Valor","Gorjetas","Combustível","Título"]; widths=[4.2*cm,2.2*cm,2.4*cm,3.0*cm,3.0*cm,3.4*cm, W-(m*2+18.2*cm)]
        c.setFont("Helvetica-Bold",10); sx=x
        for i,hname in enumerate(headers): c.drawString(sx,y,hname); sx+=widths[i]
        y-=0.5*cm; c.setFont("Helvetica",9)
        for it in items:
            sx=x
            if y < m+1.2*cm:
                c.showPage(); y=H-m-0.6*cm; c.setFont("Helvetica-Bold",10); sx=x
                for i,hname in enumerate(headers): c.drawString(sx,y,hname); sx+=widths[i]
                y-=0.5*cm; c.setFont("Helvetica",9); sx=x
            row=[it['data'], f"{it['horas']:.1f}", f"{it['km']:.1f}", f"{it['valor']:.2f}", f"{it['tips']:.2f}", f"{it['combustivel']:.2f}", it['titulo']]
            for i,cell in enumerate(row): c.drawString(sx,y,str(cell)); sx+=widths[i]
            y-=0.42*cm
        c.showPage(); c.save(); buf.seek(0)
        return send_file(buf, as_attachment=True, download_name=f"relatorio_{inicio}_{fim}.pdf", mimetype="application/pdf")

    @app.get("/relatorios/csv"); @login_required
    def reports_csv():
        inicio=request.args.get("inicio"); fim=request.args.get("fim")
        if not inicio or not fim: flash("Informe início e fim.","warning"); return redirect(url_for("reports"))
        items, tot = _query_report(inicio, fim)
        buf=io.StringIO(); w=csv.writer(buf, delimiter=';')
        w.writerow(["Início","Horas","KM","Valor","Gorjetas","Combustível","Título","Notas"])
        for it in items:
            w.writerow([it["data"], f"{it['horas']:.1f}", f"{it['km']:.1f}", f"{it['valor']:.2f}", f"{it['tips']:.2f}", f"{it['combustivel']:.2f}", it["titulo"], it["notas"]])
        w.writerow([]); w.writerow(["Totais", f"{tot['horas']:.1f}", f"{tot['km']:.1f}", f"{tot['valor']:.2f}", f"{tot['tips']:.2f}", f"{tot['combustivel']:.2f}", f"Corridas: {tot['qtd']}"])
        data=buf.getvalue().encode("utf-8-sig")
        return send_file(io.BytesIO(data), as_attachment=True, download_name=f"relatorio_{inicio}_{fim}.csv", mimetype="text/csv")

    @app.get("/relatorios/xlsx"); @login_required
    def reports_xlsx():
        inicio=request.args.get("inicio"); fim=request.args.get("fim")
        if not inicio or not fim: flash("Informe início e fim.","warning"); return redirect(url_for("reports"))
        items, tot = _query_report(inicio, fim)
        wb=Workbook(); ws=wb.active; ws.title="Relatório"
        ws.append(["Início","Horas","KM","Valor","Gorjetas","Combustível","Título","Notas"])
        for it in items:
            ws.append([it["data"], round(it["horas"],1), round(it["km"],1), round(it["valor"],2), round(it["tips"],2), round(it["combustivel"],2), it["titulo"], it["notas"]])
        ws.append([]); ws.append(["Totais", round(tot["horas"],1), round(tot["km"],1), round(tot["valor"],2), round(tot["tips"],2), round(tot["combustivel"],2), f"Corridas: {tot['qtd']}"])
        bio=io.BytesIO(); wb.save(bio); bio.seek(0)
        return send_file(bio, as_attachment=True, download_name=f"relatorio_{inicio}_{fim}.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    @app.get("/saude")
    def health(): return {"ok": True, "version": "v14.4"}

    return app
