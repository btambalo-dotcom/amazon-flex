from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from .extensions import db

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

class Shift(db.Model):
    __tablename__ = "shifts"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    hours_worked = db.Column(db.Float, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    trips = db.relationship("Trip", backref="shift", cascade="all, delete-orphan", lazy="dynamic")
    expenses = db.relationship("Expense", backref="shift", cascade="all, delete-orphan", lazy="dynamic")

class Trip(db.Model):
    __tablename__ = "trips"
    id = db.Column(db.Integer, primary_key=True)
    shift_id = db.Column(db.Integer, db.ForeignKey("shifts.id", ondelete="CASCADE"), nullable=False)
    fare_amount = db.Column(db.Float, nullable=False, default=0)
    fuel_cost = db.Column(db.Float, nullable=False, default=0)
    odometer = db.Column(db.Float, nullable=True)
    tips = db.Column(db.Float, nullable=True, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    expenses = db.relationship("Expense", backref="trip", cascade="all, delete-orphan", lazy="dynamic")

class Expense(db.Model):
    __tablename__ = "expenses"
    id = db.Column(db.Integer, primary_key=True)
    shift_id = db.Column(db.Integer, db.ForeignKey("shifts.id", ondelete="SET NULL"), nullable=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trips.id", ondelete="SET NULL"), nullable=True)
    exp_date = db.Column(db.Date, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False, default=0)
    notes = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class ScheduledRide(db.Model):
    __tablename__ = "scheduled_rides"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False, default="Amazon Flex Block")
    start_dt = db.Column(db.DateTime, nullable=False)
    end_dt = db.Column(db.DateTime, nullable=True)
    expected_block_pay = db.Column(db.Float, nullable=True)
    notes = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
