\
from flask import Blueprint, render_template, request
from datetime import datetime, timedelta
from sqlalchemy import func
from ..models import db, ScheduledRide, Expense, Station

bp = Blueprint("relatorios", __name__, url_prefix="/relatorios")

def parse_date(s):
    return datetime.strptime(s, "%Y-%m-%d")

@bp.route("/", methods=["GET"])
def index():
    # período padrão: últimos 30 dias
    fim = datetime.utcnow().date()
    inicio = fim - timedelta(days=30)
    s_in = request.args.get("inicio")
    s_fi = request.args.get("fim")
    station_id = request.args.get("station_id") or None

    if s_in and s_fi:
        inicio = parse_date(s_in).date()
        fim = parse_date(s_fi).date()

    # Consulta corridas
    q_rides = ScheduledRide.query.filter(
        ScheduledRide.inicio >= datetime.combine(inicio, datetime.min.time()),
        ScheduledRide.fim <= datetime.combine(fim, datetime.max.time()),
        ScheduledRide.exclude_from_reports.is_(False)
    )
    if station_id:
        q_rides = q_rides.filter(ScheduledRide.station_id == int(station_id))

    rides = q_rides.order_by(ScheduledRide.inicio.asc()).all()

    # Totais receita
    receita_valor = db.session.query(func.coalesce(func.sum(ScheduledRide.valor),0.0)).filter(q_rides.whereclause).scalar()
    receita_tips  = db.session.query(func.coalesce(func.sum(ScheduledRide.gorjeta),0.0)).filter(q_rides.whereclause).scalar()
    receita = float(receita_valor) + float(receita_tips)

    # Distância total
    total_milhas = db.session.query(func.coalesce(func.sum(ScheduledRide.distance_miles),0.0)).filter(q_rides.whereclause).scalar()
    total_milhas = float(total_milhas)

    # Despesas no período (todas, independente de estação)
    despesas_total = db.session.query(func.coalesce(func.sum(Expense.valor),0.0)).filter(
        Expense.data >= datetime.combine(inicio, datetime.min.time()),
        Expense.data <= datetime.combine(fim, datetime.max.time()),
    ).scalar()

    custo = float(despesas_total)
    lucro = receita - custo
    margem = (lucro/receita*100.0) if receita > 0 else 0.0
    custo_milha = (custo/total_milhas) if total_milhas > 0 else 0.0

    estacoes = Station.query.order_by(Station.nome).all()

    return render_template("relatorios/index.html",
                           inicio=inicio, fim=fim,
                           rides=rides,
                           receita=round(receita,2),
                           custo=round(custo,2),
                           lucro=round(lucro,2),
                           margem=round(margem,2),
                           total_milhas=round(total_milhas,2),
                           custo_milha=round(custo_milha,4),
                           estacoes=estacoes,
                           station_id=int(station_id) if station_id else None)
\

@bp.route("/pdf", methods=["GET"])
def pdf():
    # Gera o mesmo resumo do index, mas envia como PDF simples
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm

    # Reaproveita a lógica
    from flask import request, send_file
    from io import BytesIO

    # Parse de parâmetros
    from datetime import datetime, timedelta
    s_in = request.args.get("inicio")
    s_fi = request.args.get("fim")
    station_id = request.args.get("station_id") or None

    # padrão: últimos 30 dias
    fim_d = datetime.utcnow().date()
    inicio_d = fim_d - timedelta(days=30)
    if s_in and s_fi:
        inicio_d = datetime.strptime(s_in, "%Y-%m-%d").date()
        fim_d = datetime.strptime(s_fi, "%Y-%m-%d").date()

    # Query de corridas aplicando filtros
    from sqlalchemy import func
    q_rides = ScheduledRide.query.filter(
        ScheduledRide.inicio >= datetime.combine(inicio_d, datetime.min.time()),
        ScheduledRide.fim <= datetime.combine(fim_d, datetime.max.time()),
        ScheduledRide.exclude_from_reports.is_(False)
    )
    if station_id:
        q_rides = q_rides.filter(ScheduledRide.station_id == int(station_id))

    rides = q_rides.order_by(ScheduledRide.inicio.asc()).all()

    receita_valor = db.session.query(func.coalesce(func.sum(ScheduledRide.valor),0.0)).filter(q_rides.whereclause).scalar()
    receita_tips  = db.session.query(func.coalesce(func.sum(ScheduledRide.gorjeta),0.0)).filter(q_rides.whereclause).scalar()
    receita = float(receita_valor) + float(receita_tips)

    # Distância total
    total_milhas = db.session.query(func.coalesce(func.sum(ScheduledRide.distance_miles),0.0)).filter(q_rides.whereclause).scalar()
    total_milhas = float(total_milhas)

    despesas_total = db.session.query(func.coalesce(func.sum(Expense.valor),0.0)).filter(
        Expense.data >= datetime.combine(inicio_d, datetime.min.time()),
        Expense.data <= datetime.combine(fim_d, datetime.max.time()),
    ).scalar()
    custo = float(despesas_total)
    lucro = receita - custo
    margem = (lucro/receita*100.0) if receita>0 else 0.0

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    W, H = A4
    x, y = 20*mm, H-20*mm

    def line(text, inc=7*mm):
        nonlocal y
        c.drawString(x, y, text)
        y -= inc

    c.setFont("Helvetica-Bold", 14)
    line("Relatório - Amazon Flex")
    c.setFont("Helvetica", 11)
    line(f"Período: {inicio_d.strftime('%d/%m/%Y')} a {fim_d.strftime('%d/%m/%Y')}")
    if station_id:
        try:
            est = Station.query.get(int(station_id))
            line(f"Estação: {est.nome} ({est.codigo})" if est and est.codigo else f"Estação: {est.nome if est else '-'}")
        except Exception:
            pass

    line("")
    c.setFont("Helvetica-Bold", 12)
    line("Resumo:")
    c.setFont("Helvetica", 11)
    line(f"Receita: $ {receita:.2f}")
    line(f"Custo:   $ {custo:.2f}")
    line(f"Lucro:   $ {lucro:.2f}")
    line(f"Margem:    {margem:.2f}%")
    # total milhas
    total_milhas = 0.0
    from sqlalchemy import func
    total_milhas = float(db.session.query(func.coalesce(func.sum(ScheduledRide.distance_miles),0.0)).filter(q_rides.whereclause).scalar())
    custo_milha = (custo/total_milhas) if total_milhas>0 else 0.0
    line(f"Milhas:   {total_milhas:.2f}")
    line(f"Custo/Milha: $ {custo_milha:.4f}")

    line("")
    c.setFont("Helvetica-Bold", 12)
    line("Corridas consideradas:")
    c.setFont("Helvetica", 10)
    for r in rides:
        if y < 30*mm:
            c.showPage()
            y = H-20*mm
        est_nome = r.station.nome if r.station else "-"
        line(f"{r.inicio.strftime('%d/%m/%Y %H:%M')} - {r.fim.strftime('%H:%M')} | {est_nome} | Horas: {r.horas:.2f} | Valor: ${r.valor:.2f} | Gorjeta: ${r.gorjeta:.2f}")

    c.showPage()
    c.save()
    buffer.seek(0)
    filename = f"relatorio_{inicio_d.isoformat()}_{fim_d.isoformat()}.pdf"
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype="application/pdf")
\

@bp.route("/csv", methods=["GET"])
def csv_export():
    """Exporta CSV detalhado das corridas no período (com filtros)."""
    import csv
    from io import StringIO
    from flask import Response, request
    from datetime import datetime, timedelta

    s_in = request.args.get("inicio")
    s_fi = request.args.get("fim")
    station_id = request.args.get("station_id") or None

    fim = datetime.utcnow().date()
    inicio = fim - timedelta(days=30)
    if s_in and s_fi:
        inicio = datetime.strptime(s_in, "%Y-%m-%d").date()
        fim = datetime.strptime(s_fi, "%Y-%m-%d").date()

    q = ScheduledRide.query.filter(
        ScheduledRide.inicio >= datetime.combine(inicio, datetime.min.time()),
        ScheduledRide.fim <= datetime.combine(fim, datetime.max.time()),
        ScheduledRide.exclude_from_reports.is_(False)
    )
    if station_id:
        q = q.filter(ScheduledRide.station_id == int(station_id))
    rows = q.order_by(ScheduledRide.inicio.asc()).all()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["id","inicio","fim","horas","valor","gorjeta","milhas","estacao","exclude_from_reports"])
    for r in rows:
        est = r.station.nome if r.station else ""
        writer.writerow([r.id, r.inicio.isoformat(sep=" "), r.fim.isoformat(sep=" "), f"{r.horas:.2f}", f"{r.valor:.2f}", f"{r.gorjeta:.2f}", f"{r.distance_miles:.2f}", est, int(r.exclude_from_reports)])

    resp = Response(output.getvalue(), mimetype="text/csv")
    fname = f"corridas_{inicio.isoformat()}_{fim.isoformat()}.csv"
    resp.headers["Content-Disposition"] = f"attachment; filename={fname}"
    return resp
\

@bp.route("/estacoes", methods=["GET"])
def estacoes_compare():
    """Comparativo por estação: receita, custo (apenas despesas vinculadas às corridas da estação), lucro, margem, milhas, custo/milha."""
    from datetime import datetime, timedelta
    from sqlalchemy import func
    from flask import request

    s_in = request.args.get("inicio")
    s_fi = request.args.get("fim")

    fim = datetime.utcnow().date()
    inicio = fim - timedelta(days=30)
    if s_in and s_fi:
        inicio = datetime.strptime(s_in, "%Y-%m-%d").date()
        fim = datetime.strptime(s_fi, "%Y-%m-%d").date()

    # Todas as estações com pelo menos 1 corrida no período
    stations = db.session.query(Station).order_by(Station.nome).all()
    data = []
    for est in stations:
        q = ScheduledRide.query.filter(
            ScheduledRide.inicio >= datetime.combine(inicio, datetime.min.time()),
            ScheduledRide.fim <= datetime.combine(fim, datetime.max.time()),
            ScheduledRide.exclude_from_reports.is_(False),
            ScheduledRide.station_id == est.id
        )
        receita_val = db.session.query(func.coalesce(func.sum(ScheduledRide.valor),0.0)).filter(q.whereclause).scalar()
        receita_tip = db.session.query(func.coalesce(func.sum(ScheduledRide.gorjeta),0.0)).filter(q.whereclause).scalar()
        receita = float(receita_val) + float(receita_tip)
        milhas = float(db.session.query(func.coalesce(func.sum(ScheduledRide.distance_miles),0.0)).filter(q.whereclause).scalar())

        # custos: somente despesas ligadas a corridas dessa estação
        ride_ids = [r.id for r in q.all()]
        if ride_ids:
            custos = float(db.session.query(func.coalesce(func.sum(Expense.valor),0.0)).filter(Expense.ride_id.in_(ride_ids)).scalar())
        else:
            custos = 0.0
        lucro = receita - custos
        margem = (lucro/receita*100.0) if receita>0 else 0.0
        custo_milha = (custos/milhas) if milhas>0 else 0.0

        data.append({
            "estacao": f"{est.nome}" + (f" ({est.codigo})" if est.codigo else ""),
            "receita": round(receita,2),
            "custos": round(custos,2),
            "lucro": round(lucro,2),
            "margem": round(margem,2),
            "milhas": round(milhas,2),
            "custo_milha": round(custo_milha,4),
        })

    # Totais gerais
    q_all = ScheduledRide.query.filter(
        ScheduledRide.inicio >= datetime.combine(inicio, datetime.min.time()),
        ScheduledRide.fim <= datetime.combine(fim, datetime.max.time()),
        ScheduledRide.exclude_from_reports.is_(False)
    )
    receita_val = db.session.query(func.coalesce(func.sum(ScheduledRide.valor),0.0)).filter(q_all.whereclause).scalar()
    receita_tip = db.session.query(func.coalesce(func.sum(ScheduledRide.gorjeta),0.0)).filter(q_all.whereclause).scalar()
    receita_total = float(receita_val) + float(receita_tip)
    milhas_total = float(db.session.query(func.coalesce(func.sum(ScheduledRide.distance_miles),0.0)).filter(q_all.whereclause).scalar())

    # despesas totais (todas as despesas do período, vinculadas ou não)
    despesas_total = float(db.session.query(func.coalesce(func.sum(Expense.valor),0.0)).filter(
        Expense.data >= datetime.combine(inicio, datetime.min.time()),
        Expense.data <= datetime.combine(fim, datetime.max.time()),
    ).scalar())

    lucro_total = receita_total - despesas_total
    margem_total = (lucro_total/receita_total*100.0) if receita_total>0 else 0.0
    custo_milha_total = (despesas_total/milhas_total) if milhas_total>0 else 0.0

    return render_template("relatorios/estacoes.html",
                           inicio=inicio, fim=fim,
                           linhas=data,
                           receita_total=round(receita_total,2),
                           despesas_total=round(despesas_total,2),
                           lucro_total=round(lucro_total,2),
                           margem_total=round(margem_total,2),
                           milhas_total=round(milhas_total,2),
                           custo_milha_total=round(custo_milha_total,4))
