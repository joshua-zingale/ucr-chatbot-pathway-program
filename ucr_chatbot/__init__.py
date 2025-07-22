"""This package contains a Flask application for a tutoring chatbot,
including a public web interface and an API for interacting with the chatbot."""

from flask import Flask  # type: ignore
from typing import Mapping, Any
from pathlib import Path
import os
# from .secret import GOOGLE_CLIENT_ID, GOOGLE_SECRET, SECRET_KEY

# from .web_interface.routes import bp as bp
from authlib.integrations.flask_client import OAuth  # type: ignore
from flask_login import LoginManager  # type: ignore
from ucr_chatbot.db.models import Users, Session, engine
from ucr_chatbot.web_interface.routes import bp
from dotenv import load_dotenv


def create_app(test_config: Mapping[str, Any] | None = None):
    """Creates a Flask application for the UCR Chatbot.

    :param test_config: If specified, sets the config for the returned Flask application, defaults to None
    :return: The Flask application.
    """

    load_dotenv()

    app = Flask(__name__, instance_relative_config=True)
    app.secret_key = os.environ.get("SECRET_KEY", "fallback-dev-secret")
    app.debug = False

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    instance_path = Path(app.instance_path)
    if not instance_path.is_dir():
        instance_path.mkdir(parents=True, exist_ok=True)

    # from . import web_interface
    from . import api

    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["MAX_LOGIN_ATTEMPTS"] = 3

    login_manager = LoginManager()
    login_manager.init_app(app)  # type: ignore
    login_manager.login_view = "web_routes.login"  # type: ignore

    @login_manager.user_loader  # type: ignore
    def load_user(user_email: int):  # pyright: ignore[reportUnusedFunction]
        with Session(engine) as session:
            return session.query(Users).get(user_email)

    oauth = OAuth(app)  # type: ignore
    oauth.init_app(app)  # type: ignore

    oauth.register(  # type: ignore
        name="google",
        client_id=os.environ.get("GOOGLE_CLIENT_ID"),
        client_secret=os.environ.get("GOOGLE_SECRET"),
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid profile email"},
    )

    app.oauth = oauth  # type: ignore[attr-defined]

    # app.register_blueprint(web_interface.bp)
    app.register_blueprint(bp)
    app.register_blueprint(api.bp)

    return app