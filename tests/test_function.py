import json
from pathlib import Path

import pytest

from bot import wa

TEST_DATA_DIR = Path(__file__).parent / "data" / "requests"


@pytest.fixture(scope="module")
def message_verify():
    return _load_json(TEST_DATA_DIR / "verify_event.json")


@pytest.fixture(scope="module")
def message_read():
    return _load_json(TEST_DATA_DIR / "status_read.json")


@pytest.fixture(scope="module")
def message_received():
    return _load_json(TEST_DATA_DIR / "message.json")


def test_verify(message_verify, message_read, message_received):
    challenge = wa.verify_whatsapp_webhook(message_verify)
    assert challenge == "73736871"

    assert wa.verify_whatsapp_webhook(message_read) is None
    assert wa.verify_whatsapp_webhook(message_received) is None


def test_message(message_received, message_read):
    msg = wa.read_text_message(json.loads(message_received["body"]))
    assert msg.from_phone == "971556667777"
    assert msg.text == "hello world"

    msg = wa.read_text_message(json.loads(message_read["body"]))
    assert msg is None


def test_message_read(message_read, message_received):
    msg = wa.message_was_read(json.loads(message_read["body"]))
    assert msg.status == "read"
    assert msg.recipient == "971556667777"

    msg = wa.message_was_read(json.loads(message_received["body"]))
    assert msg is None


def _load_json(file: Path) -> dict:
    with open(file) as f:
        return json.load(f)
