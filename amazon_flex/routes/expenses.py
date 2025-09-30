\
from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from ..models import db, Expense, ScheduledRide

bp = Blueprint("expenses", __name__, url_prefix="/despesas")

def parse_date(value: str):
    return datetime.strptime(value, "%Y-%m-%d")

@bp.get("/")
def index():
    despesas = Expense.query.order_by(Expense.data.desc()).limit(200).all()
    rides = ScheduledRide.query.order_by(ScheduledRide.inicio.desc()).limit(200).all()
    return render_template("expenses/index.html", despesas=despesas, rides=rides)

@bp.route("/nova", methods=["POST"])
def nova():
    descricao = request.form.get("descricao","").strip() or None
    data = parse_date(request.form.get("data"))
    valor = float(request.form.get("valor",0) or 0)
    ride_id = request.form.get("ride_id") or None
    e = Expense(descricao=descricao, data=data, valor=valor, ride_id=int(ride_id) if ride_id else None)
    db.session.add(e)
    db.session.commit()
    flash("Despesa lançada!", "success")
    return redirect(url_for("expenses.index"))

@bp.post("/<int:id>/excluir")
def excluir(id):
    e = Expense.query.get_or_404(id)
    db.session.delete(e)
    db.session.commit()
    flash("Despesa excluída.", "success")
    return redirect(url_for("expenses.index"))
