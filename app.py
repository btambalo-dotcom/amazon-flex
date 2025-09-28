import os
from datetime import datetime, date, time
from dateutil import parser
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def instance_path():
    # Usa instance/ como local persistente (Render: monte um disk aqui)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance")

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    os.makedirs(instance_path(), exist_ok=True)
    db_path = os.path.join(instance_path(), 'flex.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        # Uploads
        app.config['UPLOAD_FOLDER'] = os.path.join(instance_path(), 'uploads')
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024  # 8MB por arquivo

    db.init_app(app)
    migrate.init_app(app, db, directory=os.path.join(os.path.dirname(__file__), 'migrations'))
        login_manager.init_app(app)

    from models import Shift, Trip  # noqa
    with app.app_context():
        db.create_all()

    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

        register_routes(app)
    return app

# ---- Models ----

    from werkzeug.security import generate_password_hash, check_password_hash
    from flask_login import UserMixin

    class User(UserMixin, db.Model):
        __tablename__ = 'users'
        id = db.Column(db.Integer, primary_key=True)
        email = db.Column(db.String(255), unique=True, nullable=False, index=True)
        password_hash = db.Column(db.String(255), nullable=False)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)

        def set_password(self, password: str):
            self.password_hash = generate_password_hash(password)

        def check_password(self, password: str) -> bool:
            return check_password_hash(self.password_hash, password)

    class ScheduledRide(db.Model):
        __tablename__ = 'scheduled_rides'
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(200), nullable=False)
        start_dt = db.Column(db.DateTime, nullable=False, index=True)
        end_dt = db.Column(db.DateTime, nullable=True)
        expected_block_pay = db.Column(db.Float, nullable=True)
        notes = db.Column(db.String(500), nullable=True)

    class Shift(db.Model):
    __tablename__ = 'shifts'
    id = db.Column(db.Integer, primary_key=True)
    work_date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=True)
    end_time = db.Column(db.Time, nullable=True)
    manual_hours = db.Column(db.Float, nullable=True)  # se quiser informar horas direto
    notes = db.Column(db.String(500), nullable=True)
    trips = db.relationship('Trip', backref='shift', cascade='all, delete-orphan')

    def hours(self):
        if self.manual_hours is not None:
            return float(self.manual_hours)
        if self.start_time and self.end_time:
            dt_start = datetime.combine(self.work_date, self.start_time)
            dt_end = datetime.combine(self.work_date, self.end_time)
            if dt_end < dt_start:
                # passou da meia-noite
                dt_end = dt_end.replace(day=dt_end.day + 1)
            return (dt_end - dt_start).total_seconds() / 3600.0
        return 0.0

    def total_earnings(self):
        return sum(t.total_earnings() for t in self.trips)

    def total_fuel(self):
        return sum(t.fuel_cost or 0 for t in self.trips)

    def total_miles(self):
        return sum(t.miles() for t in self.trips)

    def net_profit(self):
        return self.total_earnings() - self.total_fuel()


class Trip(db.Model):
    __tablename__ = 'trips'
    id = db.Column(db.Integer, primary_key=True)
    shift_id = db.Column(db.Integer, db.ForeignKey('shifts.id'), nullable=False, index=True)
    block_pay = db.Column(db.Float, nullable=False, default=0.0)   # pagamento base
    tips = db.Column(db.Float, nullable=False, default=0.0)        # gorjetas
    fuel_cost = db.Column(db.Float, nullable=True)                  # gasto de combustível
    odometer_start = db.Column(db.Integer, nullable=True)
    odometer_end = db.Column(db.Integer, nullable=True)
    notes = db.Column(db.String(500), nullable=True)

    def miles(self):
        if self.odometer_start is not None and self.odometer_end is not None:
            return max(0, self.odometer_end - self.odometer_start)
        return 0

    def total_earnings(self):
        return (self.block_pay or 0) + (self.tips or 0)

    def net_profit(self):
        return self.total_earnings() - (self.fuel_cost or 0)


# ---- Routes ----
def parse_date(val):
    if not val:
        return None
    try:
        return parser.parse(val).date()
    except Exception:
        return None

def parse_time(val):
    if not val:
        return None
    try:
        return parser.parse(val).time()
    except Exception:
        return None

def parse_float(val):
    try:
        return float(val)
    except Exception:
        return None


    def allowed_file(filename):
        if not filename or '.' not in filename: 
            return False
        ext = filename.rsplit('.', 1)[1].lower()
        return ext in {'png','jpg','jpeg','webp','pdf'}

    def 
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

        register_routes(app):
    @app.route('/uploads/<path:filename>')
        @login_required
        def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=False)

        @app.route('/')
        @login_required
    def home():
        # dashboard simples: últimos 7 dias
        today = date.today()
        start = today.fromordinal(today.toordinal()-6)
        shifts = Shift.query.filter(Shift.work_date >= start).order_by(Shift.work_date.desc()).all()
        totals = {
            'earnings': sum(s.total_earnings() for s in shifts),
            'fuel': sum(s.total_fuel() for s in shifts),
            'miles': sum(s.total_miles() for s in shifts),
            'hours': sum(s.hours() for s in shifts),
        }
        totals['net'] = totals['earnings'] - totals['fuel']
        totals['per_hour'] = (totals['net'] / totals['hours']) if totals['hours'] else 0
        totals['per_mile'] = (totals['net'] / totals['miles']) if totals['miles'] else 0
        return render_template('home.html', shifts=shifts, totals=totals, start=start, end=today)

    # ---- Shifts ----
    @app.route('/shifts')
        @login_required
    def list_shifts():
        q = Shift.query.order_by(Shift.work_date.desc()).all()
        return render_template('shifts_list.html', shifts=q)

    @app.route('/shifts/new', methods=['GET', 'POST'])
        @login_required
    def new_shift():
        if request.method == 'POST':
            work_date = parse_date(request.form.get('work_date') or '')
            start_time = parse_time(request.form.get('start_time') or '')
            end_time = parse_time(request.form.get('end_time') or '')
            manual_hours = parse_float(request.form.get('manual_hours') or '')
            notes = request.form.get('notes') or None
            if not work_date:
                flash('Informe a data do turno.', 'danger')
                return redirect(url_for('new_shift'))
            s = Shift(work_date=work_date, start_time=start_time, end_time=end_time, manual_hours=manual_hours, notes=notes)
            db.session.add(s); db.session.commit()
            flash('Turno criado!', 'success')
            return redirect(url_for('list_shifts'))
        return render_template('shift_form.html', shift=None)

    @app.route('/shifts/<int:shift_id>/edit', methods=['GET', 'POST'])
        @login_required
    def edit_shift(shift_id):
        s = Shift.query.get_or_404(shift_id)
        if request.method == 'POST':
            s.work_date = parse_date(request.form.get('work_date') or '') or s.work_date
            s.start_time = parse_time(request.form.get('start_time') or '')
            s.end_time = parse_time(request.form.get('end_time') or '')
            s.manual_hours = parse_float(request.form.get('manual_hours') or '')
            s.notes = request.form.get('notes') or None
            db.session.commit()
            flash('Turno atualizado!', 'success')
            return redirect(url_for('list_shifts'))
        return render_template('shift_form.html', shift=s)

    @app.route('/shifts/<int:shift_id>/delete', methods=['POST'])
        @login_required
    def delete_shift(shift_id):
        s = Shift.query.get_or_404(shift_id)
        db.session.delete(s); db.session.commit()
        flash('Turno removido.', 'warning')
        return redirect(url_for('list_shifts'))

    # ---- Trips ----
    @app.route('/shifts/<int:shift_id>/trips/new', methods=['GET', 'POST'])
        @login_required
    def new_trip(shift_id):
        s = Shift.query.get_or_404(shift_id)
        if request.method == 'POST':
            block_pay = parse_float(request.form.get('block_pay') or '0') or 0.0
            tips = parse_float(request.form.get('tips') or '0') or 0.0
            fuel_cost = parse_float(request.form.get('fuel_cost') or '')
            odo_start = request.form.get('odometer_start') or None
            odo_end = request.form.get('odometer_end') or None
            notes = request.form.get('notes') or None
            t = Trip(
                shift_id=s.id,
                block_pay=block_pay,
                tips=tips,
                fuel_cost=fuel_cost,
                odometer_start=int(odo_start) if odo_start else None,
                odometer_end=int(odo_end) if odo_end else None,
                notes=notes
            )
            db.session.add(t); db.session.commit()
            flash('Corrida adicionada!', 'success')
            return redirect(url_for('view_shift', shift_id=s.id))
        return render_template('trip_form.html', shift=s, trip=None)

    @app.route('/trips/<int:trip_id>/edit', methods=['GET', 'POST'])
        @login_required
    def edit_trip(trip_id):
        t = Trip.query.get_or_404(trip_id)
        if request.method == 'POST':
            t.block_pay = parse_float(request.form.get('block_pay') or '0') or 0.0
            t.tips = parse_float(request.form.get('tips') or '0') or 0.0
            t.fuel_cost = parse_float(request.form.get('fuel_cost') or '')
            odo_start = request.form.get('odometer_start') or None
            odo_end = request.form.get('odometer_end') or None
            t.odometer_start = int(odo_start) if odo_start else None
            t.odometer_end = int(odo_end) if odo_end else None
            t.notes = request.form.get('notes') or None
            db.session.commit()
            flash('Corrida atualizada!', 'success')
            return redirect(url_for('view_shift', shift_id=t.shift_id))
        return render_template('trip_form.html', shift=t.shift, trip=t)

    @app.route('/trips/<int:trip_id>/delete', methods=['POST'])
        @login_required
    def delete_trip(trip_id):
        t = Trip.query.get_or_404(trip_id)
        sid = t.shift_id
        db.session.delete(t); db.session.commit()
        flash('Corrida removida.', 'warning')
        return redirect(url_for('view_shift', shift_id=sid))

    @app.route('/shifts/<int:shift_id>')
        @login_required
    def view_shift(shift_id):
        s = Shift.query.get_or_404(shift_id)
        return render_template('shift_detail.html', shift=s)

    # ---- Reports ----
    @app.route('/reports', methods=['GET'])
        @login_required
    def reports():
        start = parse_date(request.args.get('start') or '')
        end = parse_date(request.args.get('end') or '')
        q = Shift.query
        if start:
            q = q.filter(Shift.work_date >= start)
        if end:
            q = q.filter(Shift.work_date <= end)
        shifts = q.order_by(Shift.work_date.asc()).all()
        totals = {
            'earnings': sum(s.total_earnings() for s in shifts),
            'fuel': sum(s.total_fuel() for s in shifts),
            'miles': sum(s.total_miles() for s in shifts),
            'hours': sum(s.hours() for s in shifts),
            'days': len(shifts)
        }
        totals['net'] = totals['earnings'] - totals['fuel']
        totals['per_hour'] = (totals['net'] / totals['hours']) if totals['hours'] else 0
        totals['per_mile'] = (totals['net'] / totals['miles']) if totals['miles'] else 0
        totals['per_day'] = (totals['net'] / totals['days']) if totals['days'] else 0
        return render_template('reports.html', shifts=shifts, totals=totals, start=start, end=end)

        # ---- Auth ----
        @app.route('/register', methods=['GET','POST'])
        def register():
            if request.method == 'POST':
                email = (request.form.get('email') or '').strip().lower()
                password = request.form.get('password') or ''
                if not email or not password:
                    flash('Informe e-mail e senha.', 'danger')
                    return redirect(url_for('register'))
                if User.query.filter_by(email=email).first():
                    flash('E-mail já cadastrado.', 'warning')
                    return redirect(url_for('register'))
                u = User(email=email)
                u.set_password(password)
                db.session.add(u); db.session.commit()
                flash('Conta criada! Você já pode entrar.', 'success')
                return redirect(url_for('login'))
            return render_template('auth_register.html')

        @app.route('/login', methods=['GET','POST'])
        def login():
            if request.method == 'POST':
                email = (request.form.get('email') or '').strip().lower()
                password = request.form.get('password') or ''
                u = User.query.filter_by(email=email).first()
                if not u or not u.check_password(password):
                    flash('Credenciais inválidas.', 'danger')
                    return redirect(url_for('login'))
                login_user(u, remember=True)
                flash('Bem-vindo!', 'success')
                return redirect(url_for('home'))
            return render_template('auth_login.html')

        @app.route('/logout')
        @login_required
        def logout():
            logout_user()
            flash('Até logo!', 'info')
            return redirect(url_for('login'))

        # ---- Calendar (agendamentos) ----
        @app.route('/calendar')
        @login_required
        def calendar_view():
            return render_template('calendar.html')

        @app.route('/calendar/new', methods=['GET','POST'])
        @login_required
        def calendar_new():
            if request.method == 'POST':
                title = request.form.get('title') or 'Corrida'
                start = parser.parse(request.form.get('start_dt')).replace(second=0, microsecond=0)
                end_raw = request.form.get('end_dt') or ''
                end = parser.parse(end_raw).replace(second=0, microsecond=0) if end_raw else None
                expected = parse_float(request.form.get('expected_block_pay') or '')
                notes = request.form.get('notes') or None
                ev = ScheduledRide(title=title, start_dt=start, end_dt=end, expected_block_pay=expected, notes=notes)
                db.session.add(ev); db.session.commit()
                flash('Corrida agendada!', 'success')
                return redirect(url_for('calendar_view'))
            return render_template('calendar_form.html', event=None)

        @app.route('/calendar/<int:event_id>/edit', methods=['GET','POST'])
        @login_required
        def calendar_edit(event_id):
            ev = ScheduledRide.query.get_or_404(event_id)
            if request.method == 'POST':
                ev.title = request.form.get('title') or ev.title
                ev.start_dt = parser.parse(request.form.get('start_dt')).replace(second=0, microsecond=0)
                end_raw = request.form.get('end_dt') or ''
                ev.end_dt = parser.parse(end_raw).replace(second=0, microsecond=0) if end_raw else None
                ev.expected_block_pay = parse_float(request.form.get('expected_block_pay') or '') 
                ev.notes = request.form.get('notes') or None
                db.session.commit()
                flash('Agendamento atualizado!', 'success')
                return redirect(url_for('calendar_view'))
            return render_template('calendar_form.html', event=ev)

        @app.route('/calendar/<int:event_id>/delete', methods=['POST'])
        @login_required
        def calendar_delete(event_id):
            ev = ScheduledRide.query.get_or_404(event_id)
            db.session.delete(ev); db.session.commit()
            flash('Agendamento removido.', 'warning')
            return redirect(url_for('calendar_view'))

        @app.route('/api/scheduled')
        @login_required
        def api_scheduled():
            # Return events for FullCalendar
            events = []
            for ev in ScheduledRide.query.order_by(ScheduledRide.start_dt.asc()).all():
                events.append({
                    'id': ev.id,
                    'title': ev.title,
                    'start': ev.start_dt.isoformat(),
                    'end': ev.end_dt.isoformat() if ev.end_dt else None,
                    'extendedProps': {
                        'expected_block_pay': ev.expected_block_pay,
                        'notes': ev.notes
                    }
                })
            return jsonify(events)


        @app.route('/reports/csv')
        @login_required
        def reports_csv():
            import csv, io
            start = parse_date(request.args.get('start') or '')
            end = parse_date(request.args.get('end') or '')
            q = Shift.query
            if start:
                q = q.filter(Shift.work_date >= start)
            if end:
                q = q.filter(Shift.work_date <= end)
            shifts = q.order_by(Shift.work_date.asc()).all()
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Date','Hours','Trips','Earnings','Fuel','Miles','Net','$/hour','$/mile'])
            for s in shifts:
                hours = s.hours()
                miles = s.total_miles()
                earnings = s.total_earnings()
                fuel = s.total_fuel()
                net = earnings - fuel
                per_hour = (net/hours) if hours else 0
                per_mile = (net/miles) if miles else 0
                writer.writerow([s.work_date.isoformat(), f"{hours:.2f}", len(s.trips), f"{earnings:.2f}", f"{fuel:.2f}", f"{miles:.1f}", f"{net:.2f}", f"{per_hour:.2f}", f"{per_mile:.2f}"])
            output.seek(0)
            from flask import Response
            filename = 'relatorio_flex.csv'
            return Response(output.read(), mimetype='text/csv', headers={'Content-Disposition': f'attachment; filename={filename}'})


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
