\
from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from ..models import db, ScheduledRide, Station

bp = Blueprint("rides", __name__, url_prefix="/corridas")

def parse_dt(value: str):
    # Espera formato HTML datetime-local: YYYY-MM-DDTHH:MM
    return datetime.strptime(value, "%Y-%m-%dT%H:%M")

def calcular_horas(dt_ini: datetime, dt_fim: datetime) -> float:
    if not dt_ini or not dt_fim or dt_fim <= dt_ini:
        return 0.0
    delta = dt_fim - dt_ini
    return round(delta.total_seconds()/3600.0, 2)

@bp.get("/")
def index():
    rides = ScheduledRide.query.order_by(ScheduledRide.inicio.desc()).limit(200).all()
    return render_template("rides/index.html", rides=rides)

@bp.route("/nova", methods=["GET","POST"])
def nova():
    estacoes = Station.query.order_by(Station.nome).all()
    if request.method == "POST":
        titulo = request.form.get("titulo","").strip() or None
        inicio = parse_dt(request.form["inicio"])
        fim = parse_dt(request.form["fim"])
        valor = float(request.form.get("valor",0) or 0)
        gorjeta = float(request.form.get("gorjeta",0) or 0)
        distance_miles = float(request.form.get("distance_miles",0) or 0)
        station_id = request.form.get("station_id") or None
        exclude_from_reports = bool(request.form.get("exclude_from_reports"))

        horas = calcular_horas(inicio, fim)
        ride = ScheduledRide(
            titulo=titulo, inicio=inicio, fim=fim, horas=horas,
            valor=valor, gorjeta=gorjeta,
            station_id=int(station_id) if station_id else None,
            distance_miles=distance_miles,
            exclude_from_reports=exclude_from_reports
        )
        db.session.add(ride)
        db.session.commit()
        flash("Corrida criada!", "success")
        return redirect(url_for("rides.index"))
    return render_template("rides/form.html", estacoes=estacoes, ride=None)

@bp.route("/<int:id>/editar", methods=["GET","POST"])
def editar(id):
    ride = ScheduledRide.query.get_or_404(id)
    estacoes = Station.query.order_by(Station.nome).all()
    if request.method == "POST":
        ride.titulo = request.form.get("titulo","").strip() or None
        ride.inicio = parse_dt(request.form["inicio"])
        ride.fim = parse_dt(request.form["fim"])
        ride.valor = float(request.form.get("valor",0) or 0)
        ride.gorjeta = float(request.form.get("gorjeta",0) or 0)
        ride.distance_miles = float(request.form.get("distance_miles",0) or 0)
        station_id = request.form.get("station_id") or None
        ride.station_id = int(station_id) if station_id else None
        ride.exclude_from_reports = bool(request.form.get("exclude_from_reports"))
        ride.horas = calcular_horas(ride.inicio, ride.fim)
        db.session.commit()
        flash("Corrida atualizada!", "success")
        return redirect(url_for("rides.index"))
    return render_template("rides/form.html", estacoes=estacoes, ride=ride)

@bp.post("/<int:id>/excluir")
def excluir(id):
    ride = ScheduledRide.query.get_or_404(id)
    db.session.delete(ride)
    db.session.commit()
    flash("Corrida excluída.", "success")
    return redirect(url_for("rides.index"))
