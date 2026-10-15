"""
app_factory.py – creates the Flask app and db instance.

Separated from app.py so that tests can import `db` and `create_app`
without running the server.
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

db = SQLAlchemy()


def create_app(test_config=None):
    app = Flask(__name__)

    if test_config:
        app.config.update(test_config)
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mealbridge.db"

    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    app.config.setdefault("TESTING", False)

    CORS(app)
    db.init_app(app)

    # Register route blueprints
    from routes.donations import donations_bp
    from routes.ngos import ngos_bp
    from routes.matching import matching_bp
    from routes.impact import impact_bp

    app.register_blueprint(donations_bp, url_prefix="/api")
    app.register_blueprint(ngos_bp,      url_prefix="/api")
    app.register_blueprint(matching_bp,  url_prefix="/api")
    app.register_blueprint(impact_bp,    url_prefix="/api")

    with app.app_context():
        db.create_all()

    return app
