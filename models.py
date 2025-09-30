
from flask import current_app
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, Session, scoped_session, sessionmaker
import os

Base = declarative_base()

class Station(Base):
    __tablename__ = 'stations'
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False, unique=True)

    runs = relationship('Run', back_populates='station', cascade='all, delete-orphan')

class Run(Base):
    __tablename__ = 'runs'
    id = Column(Integer, primary_key=True)
    station_id = Column(Integer, ForeignKey('stations.id'), nullable=False)
    start_dt = Column(DateTime, nullable=False)
    end_dt = Column(DateTime, nullable=False)
    hours = Column(Float, nullable=False, default=0.0)

    miles = Column(Float, default=0.0)       # milhagem
    cost = Column(Float, default=0.0)        # custo total
    revenue = Column(Float, default=0.0)     # receita bruta
    tips = Column(Float, default=0.0)        # gorjetas

    station = relationship('Station', back_populates='runs')

def get_engine():
    db_url = os.getenv('DATABASE_URL') or 'sqlite:///instance/app.db'
    if db_url.startswith('sqlite:///') and 'instance/app.db' in db_url:
        os.makedirs('instance', exist_ok=True)
    engine = create_engine(db_url, future=True)
    return engine

def init_db():
    engine = get_engine()
    Base.metadata.create_all(engine)
    return engine

def get_session():
    engine = get_engine()
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return scoped_session(factory)
