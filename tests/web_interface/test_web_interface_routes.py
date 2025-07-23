from flask.testing import FlaskClient
import io
import os
from pathlib import Path
from ucr_chatbot.db.models import upload_folder
from db.helper_functions import *
from unittest.mock import MagicMock

def test_course_selection_ok_response(client: FlaskClient):
    response = client.get('/')
    assert "200 OK" == response.status
    assert "200 OK" == response.status

def test_file_upload(client: FlaskClient, monkeypatch):
    # delete_uploads_folder()
    # clear_db()
    # initialize_db()
    # add_courses()

    mock_ollama_client = MagicMock()
    fake_embedding = [0.1, -0.2, 0.3, 0.4]
    mock_ollama_client.embeddings.return_value = {"embedding": fake_embedding}
    monkeypatch.setattr("ucr_chatbot.api.embedding.embedding.client", mock_ollama_client)

    data = {}
    data["file"] = (io.BytesIO(b"Test file for CS009A"), "test_file.txt")

    response = client.post("/course/1/documents", data=data, content_type="multipart/form-data")

    assert "200 OK" == response.status
    assert b"test_file.txt" in response.data

    app_instance = client.application
    file_path = Path(upload_folder) / "1" / "test_file.txt"
    assert file_path.exists()
    with file_path.open("rb") as f:
        assert f.read() == b"Test file for CS009A"
    file_path.unlink()


def test_file_upload_empty(client: FlaskClient):
    response = client.post("/course/1/documents", data={}, content_type="multipart/form-data")
    assert "302 FOUND" == response.status # Successful redirect


def test_file_upload_no_file(client: FlaskClient):
    data = {}
    data["file"] = (io.BytesIO(b""), "")

    response = client.post("/course/1/documents", data=data, content_type="multipart/form-data")
    assert "302 FOUND" == response.status # Successful redirect


def test_file_upload_invalid_extension(client: FlaskClient):
    data = {}
    data["file"] = (io.BytesIO(b"dog,cat,bird"), "animals.csv")

    response = client.post("/course/1/documents", data=data, content_type="multipart/form-data")

    assert "200 OK" == response.status
    assert b"You can't upload this type of file" in response.data


def test_file_download(client: FlaskClient, monkeypatch):
    mock_ollama_client = MagicMock()
    fake_embedding = [0.1, -0.2, 0.3, 0.4]
    mock_ollama_client.embeddings.return_value = {"embedding": fake_embedding}
    monkeypatch.setattr("ucr_chatbot.api.embedding.embedding.client", mock_ollama_client)

    data = {}
    data["file"] = (io.BytesIO(b"Test file for CS009A"), "test_file_download.txt")


    response = client.post("/course/1/documents", data=data, content_type="multipart/form-data")
    assert "200 OK" == response.status

    file_path_rel = Path("1") / "test_file_download.txt"
    response = client.get(f"/document/{file_path_rel}/download")

    assert "200 OK" == response.status
    assert response.data == b"Test file for CS009A"

    file_path_abs = Path(upload_folder) / file_path_rel
    assert file_path_abs.exists()
    with file_path_abs.open("rb") as f:
        assert f.read() == b"Test file for CS009A"

    response = client.get("/")
    assert "200 OK" == response.status

    file_path_abs.unlink()


def test_file_delete(client: FlaskClient, monkeypatch):
    mock_ollama_client = MagicMock()
    fake_embedding = [0.1, -0.2, 0.3, 0.4]
    mock_ollama_client.embeddings.return_value = {"embedding": fake_embedding}
    monkeypatch.setattr("ucr_chatbot.api.embedding.embedding.client", mock_ollama_client)

    data = {}
    data["file"] = (io.BytesIO(b"Test file for CS009A"), "test_file_delete.txt")

    response = client.post("/course/1/documents", data=data, content_type="multipart/form-data")
    assert "200 OK" == response.status

    file_path_rel = Path("1") / "test_file_delete.txt"

    response = client.post(f"document/{file_path_rel}/delete")

    assert "302 FOUND" == response.status

    full_path = Path(upload_folder) / file_path_rel
    assert full_path.exists()
    with full_path.open("rb") as f:
        assert f.read() == b"Test file for CS009A"
    full_path.unlink()


def test_chatroom_conversation_flow(client: FlaskClient):
    from ucr_chatbot.db.models import add_new_user, add_new_course

    add_new_user("test@ucr.edu", "Test", "User")
    add_new_course("Test Course")
    course_id = 1
    init_message = "Hello, I need help with my homework."
    response = client.post(
        f"/conversation/new/{course_id}/chat",
        json={"type": "create", "message": init_message},
        headers={"Accept": "application/json"}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "conversationId" in data
    conversation_id = data["conversationId"]

    response = client.post(
        f"/conversation/{conversation_id}",
        json={"type": "reply", "message": init_message},
        headers={"Accept": "application/json"}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "reply" in data
    assert isinstance(data["reply"], str)
    assert len(data["reply"]) > 0

    followup_message = "Can you explain recursion?"
    response = client.post(
        f"/conversation/{conversation_id}",
        json={"type": "send", "message": followup_message},
        headers={"Accept": "application/json"}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "200"

    response = client.post(
        f"/conversation/{conversation_id}",
        json={"type": "reply", "message": followup_message},
        headers={"Accept": "application/json"}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "reply" in data
    assert isinstance(data["reply"], str)
    assert len(data["reply"]) > 0
