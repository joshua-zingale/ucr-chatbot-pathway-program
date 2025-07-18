from flask.testing import FlaskClient
import io
import os
from ucr_chatbot.db.models import upload_folder
from db.helper_functions import *
from unittest.mock import MagicMock
from sqlalchemy.engine import Connection
from sqlalchemy import insert


def test_course_selection_ok_response(client: FlaskClient):
    response = client.get('/')
    assert "200 OK" == response.status
    assert b"<h1>ScotGPT</h1>" in response.data

def test_new_conversation_ok_response(client: FlaskClient):
    response = client.get('/conversation/new/10/chat')
    assert "200 OK" == response.status
    assert b"<h2>CONVERSATIONS</h2>" in response.data

def test_conversation_ok_response(client: FlaskClient, db: Connection):
    insert_user = insert(Users).values(email="test@ucr.edu", first_name="John", last_name="Doe")
    db.execute(insert_user)


    insert_course = insert(Courses).values(id=100, name="CS010")
    db.execute(insert_course)


    insert_conv = insert(Conversations).values(id=10, initiated_by="test@ucr.edu", course_id=100)
    db.execute(insert_conv)

    db.commit()  
    response = client.get('/conversation/10')

    assert response.status_code == 200
    assert b"<h2>CONVERSATIONS</h2>" in response.data
