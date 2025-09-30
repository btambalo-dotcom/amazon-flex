\
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Station(db.Model):
    __tablename__ = "stations"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False, unique=True)
    codigo = db.Column(db.String(32), nullable=True)
    endereco = db.Column(db.String(255), nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

class ScheduledRide(db.Model):
    __tablename__ = "scheduled_rides"
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(160), nullable=True)
    inicio = db.Column(db.DateTime, nullable=False)
    fim = db.Column(db.DateTime, nullable=False)
    horas = db.Column(db.Float, nullable=False, default=0.0)
    valor = db.Column(db.Float, nullable=False, default=0.0)     # Recebido da corrida
    gorjeta = db.Column(db.Float, nullable=False, default=0.0)   # Tips
    distance_miles = db.Column(db.Float, nullable=False, default=0.0)  # Distância percorrida na corrida
    exclude_from_reports = db.Column(db.Boolean, nullable=False, server_default="0")
    # Relação com estação
    station_id = db.Column(db.Integer, db.ForeignKey("stations.id", ondelete="SET NULL"))
    station = db.relationship("Station", lazy="joined")
    # Expenses children
    expenses = db.relationship("Expense", backref="ride", cascade="all, delete-orphan", passive_deletes=True)

class Expense(db.Model):
    __tablename__ = "expenses"
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(160), nullable=True)
    data = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    valor = db.Column(db.Float, nullable=False, default=0.0)
    ride_id = db.Column(db.Integer, db.ForeignKey("scheduled_rides.id", ondelete="CASCADE"), nullable=True)

def ensure_schema():
    """Cria colunas ausentes de forma simples (sem Alembic)"""
    from sqlalchemy import inspect, text
    insp = inspect(db.engine)

    # Tabelas
    tables = insp.get_table_names()
    expected = {"stations","scheduled_rides","expenses"}
    if not expected.issubset(set(tables)):
        db.create_all()

    # scheduled_rides.station_id
    cols = [c["name"] for c in insp.get_columns("scheduled_rides")]
    if "station_id" not in cols:
        db.session.execute(text("ALTER TABLE scheduled_rides ADD COLUMN station_id INTEGER"))
        db.session.commit()
    # scheduled_rides.distance_miles
    cols = [c['name'] for c in insp.get_columns('scheduled_rides')]
    if 'distance_miles' not in cols:
        db.session.execute(text("ALTER TABLE scheduled_rides ADD COLUMN distance_miles FLOAT DEFAULT 0.0 NOT NULL"))
        db.session.commit()

    # scheduled_rides.exclude_from_reports
    cols = [c["name"] for c in insp.get_columns("scheduled_rides")]
    if "exclude_from_reports" not in cols:
        db.session.execute(text("ALTER TABLE scheduled_rides ADD COLUMN exclude_from_reports BOOLEAN DEFAULT 0 NOT NULL"))
        db.session.commit()
    # expenses.ride_id
    cols = [c["name"] for c in insp.get_columns("expenses")]
    if "ride_id" not in cols:
        db.session.execute(text("ALTER TABLE expenses ADD COLUMN ride_id INTEGER"))
        db.session.commit()
