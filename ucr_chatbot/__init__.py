"""This package contains a Flask application for a tutoring chatbot,
including a public web interface and an API for interacting with the chatbot."""

from flask import Flask
from typing import Mapping, Any
import os


def create_app(test_config: Mapping[str, Any] | None = None):
    """Creates a Flask application for the UCR Chatbot.

    :param test_config: If specified, sets the config for the returned Flask application, defaults to None
    :return: The Flask application.
    """
    upload_folder: str = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "uploads"
    )
    courses: list[str] = [
        "CS009A",
        "CS009B",
        "CS009C",
        "CS010A",
        "CS010B",
        "CS010C",
        "CS011",
        "CS061",
        "CS100",
        "CS111",
        "CS141",
    ]

    app = Flask(__name__, instance_relative_config=True)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    app.config["UPLOAD_FOLDER"] = upload_folder

    # uploads folder is created
    if not os.path.isdir(upload_folder):
        os.makedirs(upload_folder)
        for course in courses:
            os.makedirs(os.path.join(upload_folder, course))

    # ensure the instance folder exists
    if not os.path.isdir(app.instance_path):
        os.makedirs(app.instance_path)

    from . import web_interface
    from . import api

    app.register_blueprint(web_interface.bp)
    app.register_blueprint(api.bp)

    return app
