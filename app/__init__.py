import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def instance_path():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "instance")
    os.makedirs(p, exist_ok=True)
    os.makedirs(os.path.join(p, "uploads"), exist_ok=True)
    return p

def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "devkey")

    uri = os.environ.get("SQLALCHEMY_DATABASE_URI")
    if not uri:
        db_filename = os.environ.get("DB_FILE", "flex.db")
        db_path = os.path.join(instance_path(), db_filename)
        uri = f"sqlite:///{db_path}"

    app.config["SQLALCHEMY_DATABASE_URI"] = uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    migrate.init_app(app, db)

    @app.route("/")
    def index():
        return "Amazon Flex Tracker v10.1 rodando com sucesso!"

    return app
