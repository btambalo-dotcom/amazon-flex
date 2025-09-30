
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
import os
from datetime import datetime
from models import init_db, get_session, Station, Run
from forms import StationForm, RunForm

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key')

# Inicializa banco
init_db()
Session = get_session()

def calc_margin(total_revenue, total_tips, total_cost):
    lucro = (total_revenue or 0) + (total_tips or 0) - (total_cost or 0)
    base = (total_revenue or 0)
    if base <= 0:
        return 0.0, lucro
    return round((lucro / base) * 100.0, 2), round(lucro, 2)

@app.route('/')
def index():
    return render_template('index.html')

# ---------- ESTAÇÕES ----------
@app.route('/stations')
def stations():
    with Session() as s:
        stations = s.query(Station).order_by(Station.name.asc()).all()
    return render_template('stations.html', stations=stations)

@app.route('/stations/new', methods=['GET', 'POST'])
def station_new():
    form = StationForm()
    if form.validate_on_submit():
        with Session() as s:
            s.add(Station(name=form.name.data.strip()))
            s.commit()
        flash('Estação criada com sucesso!', 'success')
        return redirect(url_for('stations'))
    return render_template('station_form.html', form=form, title='Nova Estação')

@app.route('/stations/<int:station_id>/edit', methods=['GET', 'POST'])
def station_edit(station_id):
    with Session() as s:
        st = s.get(Station, station_id)
        if not st:
            flash('Estação não encontrada.', 'danger')
            return redirect(url_for('stations'))
        form = StationForm(obj=st)
        if form.validate_on_submit():
            st.name = form.name.data.strip()
            s.commit()
            flash('Estação atualizada!', 'success')
            return redirect(url_for('stations'))
    return render_template('station_form.html', form=form, title='Editar Estação')

@app.route('/stations/<int:station_id>/delete', methods=['POST'])
def station_delete(station_id):
    with Session() as s:
        st = s.get(Station, station_id)
        if st:
            s.delete(st)
            s.commit()
            flash('Estação removida.', 'warning')
    return redirect(url_for('stations'))

# ---------- CORRIDAS ----------
@app.route('/runs')
def runs():
    with Session() as s:
        data = s.query(Run).order_by(Run.start_dt.desc()).all()
        stations = s.query(Station).order_by(Station.name.asc()).all()
    return render_template('runs.html', runs=data, stations=stations)

@app.route('/runs/new', methods=['GET', 'POST'])
def run_new():
    form = RunForm()
    with Session() as s:
        form.station_id.choices = [(st.id, st.name) for st in s.query(Station).order_by(Station.name.asc()).all()]
    if form.validate_on_submit():
        with Session() as s:
            start_dt = form.start_dt.data
            end_dt = form.end_dt.data
            hours = round((end_dt - start_dt).total_seconds() / 3600.0, 2)
            run = Run(
                station_id=form.station_id.data,
                start_dt=start_dt,
                end_dt=end_dt,
                hours=hours,
                miles=form.miles.data or 0.0,
                cost=form.cost.data or 0.0,
                revenue=form.revenue.data or 0.0,
                tips=form.tips.data or 0.0,
            )
            s.add(run)
            s.commit()
            flash(f'Corrida criada. Horas calculadas: {hours}h', 'success')
            return redirect(url_for('runs'))
    return render_template('run_form.html', form=form, title='Nova Corrida')

@app.route('/runs/<int:run_id>/edit', methods=['GET', 'POST'])
def run_edit(run_id):
    with Session() as s:
        run = s.get(Run, run_id)
        if not run:
            flash('Corrida não encontrada.', 'danger')
            return redirect(url_for('runs'))
        form = RunForm(obj=run)
        form.station_id.choices = [(st.id, st.name) for st in s.query(Station).order_by(Station.name.asc()).all()]
        if form.validate_on_submit():
            run.station_id = form.station_id.data
            run.start_dt = form.start_dt.data
            run.end_dt = form.end_dt.data
            run.hours = round((run.end_dt - run.start_dt).total_seconds() / 3600.0, 2)
            run.miles = form.miles.data or 0.0
            run.cost = form.cost.data or 0.0
            run.revenue = form.revenue.data or 0.0
            run.tips = form.tips.data or 0.0
            s.commit()
            flash('Corrida atualizada.', 'success')
            return redirect(url_for('runs'))
    return render_template('run_form.html', form=form, title='Editar Corrida')

@app.route('/runs/<int:run_id>/delete', methods=['POST'])
def run_delete(run_id):
    with Session() as s:
        run = s.get(Run, run_id)
        if run:
            s.delete(run)
            s.commit()
            flash('Corrida removida.', 'warning')
    return redirect(url_for('runs'))

# ---------- RELATÓRIOS ----------
@app.route('/reports', methods=['GET', 'POST'])
def reports():
    with Session() as s:
        stations = s.query(Station).order_by(Station.name.asc()).all()

    station_id = request.values.get('station_id', type=int)
    start = request.values.get('start')
    end = request.values.get('end')
    action_delete_before = request.values.get('delete_before')  # data para excluir corridas anteriores

    # Exclusão de corridas mais antigas que uma data
    if action_delete_before and request.method == 'POST':
        try:
            cut = datetime.strptime(action_delete_before, '%Y-%m-%d')
            with Session() as s:
                q = s.query(Run).filter(Run.start_dt < cut)
                deleted = q.delete(synchronize_session=False)
                s.commit()
            flash(f'{deleted} corrida(s) anteriores a {cut.date()} foram excluídas.', 'warning')
        except Exception as e:
            flash('Data inválida para exclusão.', 'danger')

    qparams = {}
    with Session() as s:
        q = s.query(Run)
        if station_id:
            q = q.filter(Run.station_id == station_id)
        if start:
            try:
                start_dt = datetime.strptime(start, '%Y-%m-%d')
                q = q.filter(Run.start_dt >= start_dt)
                qparams['start'] = start
            except:
                pass
        if end:
            try:
                end_dt = datetime.strptime(end, '%Y-%m-%d')
                q = q.filter(Run.end_dt <= end_dt)
                qparams['end'] = end
            except:
                pass
        data = q.order_by(Run.start_dt.asc()).all()

    # Agregados
    total_hours = round(sum(r.hours for r in data), 2)
    total_miles = round(sum((r.miles or 0) for r in data), 2)
    total_revenue = round(sum((r.revenue or 0) for r in data), 2)
    total_tips = round(sum((r.tips or 0) for r in data), 2)
    total_cost = round(sum((r.cost or 0) for r in data), 2)
    margin_pct, lucro = calc_margin(total_revenue, total_tips, total_cost)

    return render_template(
        'reports.html',
        runs=data,
        stations=stations,
        sel_station=station_id,
        start=start or '',
        end=end or '',
        totals=dict(
            hours=total_hours,
            miles=total_miles,
            revenue=total_revenue,
            tips=total_tips,
            cost=total_cost,
            lucro=lucro,
            margin_pct=margin_pct,
        )
    )

if __name__ == '__main__':
    app.run(debug=True)
