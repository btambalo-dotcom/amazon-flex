\
from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..models import db, Station

bp = Blueprint("stations", __name__, url_prefix="/estacoes")

@bp.get("/")
def index():
    estacoes = Station.query.order_by(Station.nome).all()
    return render_template("stations/index.html", estacoes=estacoes)

@bp.route("/nova", methods=["GET","POST"])
def nova():
    if request.method == "POST":
        nome = request.form.get("nome","").strip()
        codigo = request.form.get("codigo","").strip() or None
        endereco = request.form.get("endereco","").strip() or None
        if not nome:
            flash("Nome é obrigatório.", "warning")
        else:
            db.session.add(Station(nome=nome, codigo=codigo, endereco=endereco))
            db.session.commit()
            flash("Estação criada!", "success")
            return redirect(url_for("stations.index"))
    return render_template("stations/form.html")

@bp.route("/<int:id>/editar", methods=["GET","POST"])
def editar(id):
    e = Station.query.get_or_404(id)
    if request.method == "POST":
        e.nome = request.form.get("nome","").strip()
        e.codigo = request.form.get("codigo","").strip() or None
        e.endereco = request.form.get("endereco","").strip() or None
        db.session.commit()
        flash("Estação atualizada!", "success")
        return redirect(url_for("stations.index"))
    return render_template("stations/form.html", estacao=e)

@bp.post("/<int:id>/excluir")
def excluir(id):
    e = Station.query.get_or_404(id)
    db.session.delete(e)
    db.session.commit()
    flash("Estação excluída.", "success")
    return redirect(url_for("stations.index"))
