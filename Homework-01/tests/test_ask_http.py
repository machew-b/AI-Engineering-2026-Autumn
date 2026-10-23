"""Run the real google-genai SDK against a tiny local fake Gemini server.

This checks what the mocks in test_ask.py cannot: that the history really is
serialized into the HTTP request body (roles and parts) and that the SDK parses
usageMetadata into the field names app/ask.py reads. No internet, no API key.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from google import genai
from google.genai import types

from app.ask import Conversation


class _Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.server.requests.append({"path": self.path, "body": body})
        n = len(self.server.requests)
        reply = {
            "candidates": [
                {"content": {"role": "model", "parts": [{"text": f"answer {n}"}]}, "finishReason": "STOP", "index": 0}
            ],
            "usageMetadata": {
                "promptTokenCount": 10 * n,
                "candidatesTokenCount": 3,
                "thoughtsTokenCount": 2,
                "totalTokenCount": 10 * n + 5,
            },
            "modelVersion": "fake",
        }
        payload = json.dumps(reply).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):
        pass


@pytest.fixture
def fake_gemini():
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    server.requests = []
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    server.server_close()


def test_history_reaches_the_wire_and_usage_is_parsed(fake_gemini):
    client = genai.Client(
        api_key="test-key-not-real",
        http_options=types.HttpOptions(base_url=f"http://127.0.0.1:{fake_gemini.server_port}"),
    )
    conversation = Conversation(client, model="fake-model")

    assert conversation.send("first question") == "answer 1"
    assert conversation.send("follow-up") == "answer 2"

    first, second = (r["body"]["contents"] for r in fake_gemini.requests)
    assert [c["role"] for c in first] == ["user"]
    assert [c["role"] for c in second] == ["user", "model", "user"]
    assert [c["parts"][0]["text"] for c in second] == ["first question", "answer 1", "follow-up"]
    assert "fake-model" in fake_gemini.requests[0]["path"]

    assert conversation.last_usage.input == 20
    assert conversation.last_usage.output == 3
    assert conversation.last_usage.thinking == 2
    assert conversation.total_usage.input == 30
