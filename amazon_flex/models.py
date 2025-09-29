
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from .extensions import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    def set_password(self, p): self.password_hash = generate_password_hash(p)
    def check_password(self, p): return check_password_hash(self.password_hash, p)

class Shift(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    hours_worked = db.Column(db.Float, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shift_id = db.Column(db.Integer, nullable=True)
    fare_amount = db.Column(db.Float, nullable=False, default=0)
    fuel_cost = db.Column(db.Float, nullable=False, default=0)
    odometer = db.Column(db.Float)
    tips = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exp_date = db.Column(db.Date, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False, default=0)
    notes = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class ScheduledRide(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False, default="Corrida Amazon Flex")
    start_dt = db.Column(db.DateTime, nullable=False)
    end_dt = db.Column(db.DateTime)
    hours_planned = db.Column(db.Float)
    expected_block_pay = db.Column(db.Float)
    tips = db.Column(db.Float)
    fuel_cost = db.Column(db.Float)
    odometer_start = db.Column(db.Float)
    odometer_end = db.Column(db.Float)
    notes = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
