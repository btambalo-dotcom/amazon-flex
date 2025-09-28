from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    db_file = os.getenv("DB_FILE", "flex.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///instance/{db_file}"
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "default_key")

    db.init_app(app)
    migrate.init_app(app, db)

    from models import User, Trip, Shift

    @app.route("/")
    def index():
        return "Amazon Flex Tracker Online!"

    return app
