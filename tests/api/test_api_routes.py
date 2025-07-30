import pytest
import json
from unittest.mock import MagicMock

def test_generate_non_stream_success(client, monkeypatch):
    """
    Tests a successful non-streaming POST request to /generate.
    """
    # 1. Mock the dependencies that the route calls
    mock_llm_client = MagicMock()
    mock_retriever = MagicMock()

    # Configure the return values for the mocked dependencies
    mock_retriever.get_segments_for.return_value = [MagicMock(id=10, text="fact 1")]
    mock_llm_client.get_response.return_value = "Mocked LLM response."

    # Use monkeypatch to replace the real objects with our mocks
    monkeypatch.setattr("ucr_chatbot.api.routes.client", mock_llm_client)
    monkeypatch.setattr("ucr_chatbot.api.routes.retriever", mock_retriever)

    # 2. Make the request to the endpoint
    response = client.post(
        '/api/generate',
        json={"prompt": "What is Python?", "conversation_id": 55}
    )

    # 3. Assert the results
    assert response.status_code == 200
    response_data = response.get_json()
    assert response_data["text"] == "Mocked LLM response."
    assert response_data["conversation_id"] == 55
    assert response_data["sources"] == [{"segment_id": 10}]


def test_generate_stream_success(client, monkeypatch):
    """
    Tests a successful streaming POST request to /generate.
    """
    mock_llm_client = MagicMock()
    mock_retriever = MagicMock()

    mock_retriever.get_segments_for.return_value = []
    mock_llm_client.stream_response.return_value = iter(["Mock ", "stream."])

    monkeypatch.setattr("ucr_chatbot.api.routes.client", mock_llm_client)
    monkeypatch.setattr("ucr_chatbot.api.routes.retriever", mock_retriever)

    response = client.post(
        '/api/generate',
        json={"prompt": "Tell me a story", "stream": True, "conversation_id": 56}
    )

    assert response.status_code == 200
    assert response.mimetype == "text/event-stream"
    # Verify the server-sent event formatting
    expected_data = 'data: {"text": "Mock "}\n\ndata: {"text": "stream."}\n\n'
    assert response.get_data(as_text=True) == expected_data


def test_generate_passes_parameters_to_client(client, monkeypatch):
    """
    Tests that optional parameters are correctly extracted from the JSON
    and passed to the language model client.
    """
    mock_llm_client = MagicMock()
    mock_llm_client.get_response.return_value = "mocked llm response"
    mock_retriever = MagicMock()
    mock_retriever.get_segments_for.return_value = []
    monkeypatch.setattr("ucr_chatbot.api.routes.client", mock_llm_client)
    monkeypatch.setattr("ucr_chatbot.api.routes.retriever", mock_retriever)

    client.post(
        '/api/generate',
        json={
            "prompt": "test",
            "temperature": 0.99,
            "max_tokens": 512,
            "stop_sequences": ["\n", "User:"]
        }
    )

    # Assert that the client's get_response method was called once
    mock_llm_client.get_response.assert_called_once()
    # Inspect the keyword arguments of that call
    _, call_kwargs = mock_llm_client.get_response.call_args
    assert call_kwargs['temperature'] == 0.99
    assert call_kwargs['max_tokens'] == 512
    assert call_kwargs['stop_sequences'] == ["\n", "User:"]


def test_generate_with_all_parameters(client, monkeypatch):
    """
    Tests the /api/generate endpoint with ALL valid parameters to ensure
    comprehensive coverage of the API functionality.
    """
    # Mock the dependencies
    mock_llm_client = MagicMock()
    mock_retriever = MagicMock()

    # Configure mock return values
    mock_segments = [
        MagicMock(id=1, text="First relevant context"),
        MagicMock(id=2, text="Second relevant context"),
        MagicMock(id=3, text="Third relevant context")
    ]
    mock_retriever.get_segments_for.return_value = mock_segments
    mock_llm_client.get_response.return_value = "Comprehensive test response with all parameters."

    # Apply mocks
    monkeypatch.setattr("ucr_chatbot.api.routes.client", mock_llm_client)
    monkeypatch.setattr("ucr_chatbot.api.routes.retriever", mock_retriever)

    # Test with ALL valid parameters
    request_data = {
        "prompt": "What is the difference between Python and JavaScript?",
        "conversation_id": 12345,
        "stream": False,
        "temperature": 0.7,
        "max_tokens": 1500,
        "stop_sequences": ["\n\n", "Question:", "Answer:"]
    }

    response = client.post('/api/generate', json=request_data)

    # Assert response status and structure
    assert response.status_code == 200
    response_data = response.get_json()
    
    # Verify response contains expected fields
    assert "text" in response_data
    assert "sources" in response_data
    assert "conversation_id" in response_data
    
    # Verify response values
    assert response_data["text"] == "Comprehensive test response with all parameters."
    assert response_data["conversation_id"] == 12345
    assert response_data["sources"] == [
        {"segment_id": 1},
        {"segment_id": 2}, 
        {"segment_id": 3}
    ]

    # Verify that retriever was called with correct parameters
    mock_retriever.get_segments_for.assert_called_once_with(
        "What is the difference between Python and JavaScript?", 
        num_segments=3
    )

    # Verify that LLM client was called with all parameters
    mock_llm_client.get_response.assert_called_once()
    _, call_kwargs = mock_llm_client.get_response.call_args
    
    # Check that the prompt includes the system prompt formatting
    assert "Main directive" in call_kwargs['prompt']
    assert "Context" in call_kwargs['prompt']
    assert "Question" in call_kwargs['prompt']
    assert "What is the difference between Python and JavaScript?" in call_kwargs['prompt']
    
    # Verify all parameters were passed correctly
    assert call_kwargs['max_tokens'] == 1500
    assert call_kwargs['temperature'] == 0.7
    assert call_kwargs['stop_sequences'] == ["\n\n", "Question:", "Answer:"]


def test_generate_missing_prompt_returns_400(client):
    """
    Tests that a 400 Bad Request error is returned if 'prompt' is missing.
    """
    response = client.post('/api/generate', json={"conversation_id": 1})
    assert response.status_code == 400
    response_data = response.get_json()
    assert "Missing 'prompt' in request" in response_data["error"]


def test_generate_invalid_json_returns_400(client):
    """
    Tests that a 400 Bad Request error is returned for a non-JSON request body.
    """
    response = client.post(
        '/api/generate',
        data="this is not json",
        content_type="text/plain"
    )
    assert response.status_code == 415
