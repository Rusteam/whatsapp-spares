import json
from pathlib import Path

import pytest

from bot import wa

TEST_DATA_DIR = Path(__file__).parent / "data" / "requests"


@pytest.fixture(scope="module")
def message_verify():
    return {
        "queryStringParameters": {
            "hub.challenge": "73736871",
            "hub.mode": "subscribe",
            "hub.verify_token": "HAPPY_CODING",
        }
    }


@pytest.fixture(scope="module")
def message_read():
    return {
        "queryStringParameters": {},
        "body": '{"object":"whatsapp_business_account","entry":[{"id":"105650032446631","changes":[{"value":{"messaging_product":"whatsapp","metadata":{"display_phone_number":"15550668492","phone_number_id":"108587615483446"},"statuses":[{"id":"wamid.HBgMOTcxNTU2NzY2MTc3FQIAERgSMDlCREFFRjI1QkUzQjY4RDU0AA==","status":"read","timestamp":"1675909679","recipient_id":"971556667777"}]},"field":"messages"}]}]}',
    }


@pytest.fixture(scope="module")
def message_received():
    return {
        "queryStringParameters": {},
        "body": '{"object":"whatsapp_business_account","entry":[{"id":"1111122222221","changes":[{"value":{"messaging_product":"whatsapp","metadata":{"display_phone_number":"1555555555","phone_number_id":"108108108108108"},"contacts":[{"profile":{"name":"Test User"},"wa_id":"971556667777"}],"messages":[{"from":"971556667777","id":"wamid.HBgMOTcxNTU2NzY2MTc3FQIAEhgUM0VCMDVENEM1QTUzNEI0RDI0NjYA","timestamp":"1675825342","text":{"body":"hello world"},"type":"text"}]},"field":"messages"}]}]}',
    }


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
