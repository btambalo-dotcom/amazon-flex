
import os
from flask import Flask
from extensions import db, migrate

def create_app():
    app = Flask(__name__)

    db_file = os.getenv("DB_FILE", "flex.db")
    app.config.update(
        SQLALCHEMY_DATABASE_URI=f"sqlite:///instance/{db_file}",
        SECRET_KEY=os.getenv("SECRET_KEY", "change-me"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    db.init_app(app)
    migrate.init_app(app, db)

    # Import models after db init to avoid circular imports
    from models import User, Shift, Trip  # noqa: F401

    @app.get("/health")
    def health():
        return {"ok": True, "version": "v13.2"}

    @app.get("/")
    def index():
        return "Amazon Flex Tracker v13.2 is running!"

    return app
