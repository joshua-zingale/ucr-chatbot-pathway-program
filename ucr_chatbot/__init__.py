"""This package contains a Flask application for a tutoring chatbot,
including a public web interface and an API for interacting with the chatbot."""

from flask import Flask
from typing import Mapping, Any
import os
from .secret import GOOGLE_CLIENT_ID, GOOGLE_SECRET, SECRET_KEY
from .web_interface.routes import bp as web_bp
from authlib.integrations.flask_client import OAuth 
from flask_login import LoginManager
from ucr_chatbot.db.models import Users, Session, engine

def create_app(test_config: Mapping[str, Any] | None = None):
    """Creates a Flask application for the UCR Chatbot.

    :param test_config: If specified, sets the config for the returned Flask application, defaults to None
    :return: The Flask application.
    """

    app = Flask(__name__, instance_relative_config=True)
    app.secret_key = SECRET_KEY
    app.debug = False

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    if not os.path.isdir(app.instance_path):
        os.makedirs(app.instance_path)

    from . import web_interface
    from . import api

    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_HTTPONLY"] = True

    login_manager = LoginManager()
    login_manager.init_app(app)  # type: ignore
    login_manager.login_view = "web_routes.login"  # type: ignore

    @login_manager.user_loader  # type: ignore
    def load_user(user_email: int):  # pyright: ignore[reportUnusedFunction]
        with Session(engine) as session:
            return session.query(Users).get(user_email)

    oauth = OAuth(app)  # type: ignore
    oauth.init_app(app)

    oauth.register(  # type: ignore
        name="google",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid profile email"},
    )

    app.oauth = oauth  # type: ignore[attr-defined]

    app.register_blueprint(web_interface.bp)
    app.register_blueprint(api.bp)

    return app
