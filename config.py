import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_FILE = os.getenv("DB_FILE", "flex.db")

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "secret-key")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'instance', DB_FILE)}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
