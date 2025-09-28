
import os
from flask import Flask
from extensions import db, migrate

def create_app():
    app = Flask(__name__)

    # ensure instance directory exists for sqlite
    os.makedirs("instance", exist_ok=True)

    db_file = os.getenv("DB_FILE", "flex.db")
    db_path = os.path.join("instance", db_file)

    app.config.update(
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{db_path}",
        SECRET_KEY=os.getenv("SECRET_KEY", "change-me"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    db.init_app(app)
    migrate.init_app(app, db)

    # import models after db init to avoid circular imports
    from models import User, Shift, Trip  # noqa: F401

    @app.get("/")
    def home():
        return "Amazon Flex Tracker v13.3 OK"

    @app.get("/health")
    def health():
        return {"ok": True, "db_file": db_file, "version": "v13.3"}

    return app
