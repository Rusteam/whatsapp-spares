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
        "body": '{"object":"whatsapp_business_account","entry":[{"id":"105","changes":[{"value":{'
        '"messaging_product":"whatsapp","metadata":{"display_phone_number":"155","phone_number_id":"1085"},'
        '"statuses":[{"id":"wamid.HBgM=","status":"read","timestamp":"1675909679","recipient_id":"9715"}]},'
        '"field":"messages"}]}]}',
    }


@pytest.fixture(scope="module")
def message_text():
    return {
        "queryStringParameters": {},
        "body": '{"object":"whatsapp_business_account","entry":[{"id":"111","changes":[{"value":{'
        '"messaging_product":"whatsapp","metadata":{"display_phone_number":"155","phone_number_id":"108"},'
        '"contacts":[{"profile":{"name":"Test User"},"wa_id":"9715"}],"messages":[{"from":"9715",'
        '"id":"wamid.HBgM","timestamp":"1675825342","text":{"body":"hello world"},"type":"text"}]},'
        '"field":"messages"}]}]}',
    }


@pytest.fixture(scope="module")
def message_media_image():
    return {
        "queryStringParameters": {},
        "body": '{"object":"whatsapp_business_account","entry":[{"id":"1056","changes":[{"value":{'
        '"messaging_product":"whatsapp","metadata":{"display_phone_number":"1555","phone_number_id":"1085"},'
        '"contacts":[{"profile":{"name":"Test User"},"wa_id":"9715"}],"messages":[{"context":{'
        '"forwarded":true},"from":"9715","id":"wamid.HBgM=","timestamp":"1686277037","type":"image",'
        '"image":{"caption":"15 days order","mime_type":"image\\/jpeg","sha256":"vZjyK=","id":"2295"}}]},'
        '"field":"messages"}]}]}',
    }


@pytest.fixture(scope="module")
def message_media_video():
    return {
        "queryStringParameters": {},
        "body": '{"object":"whatsapp_business_account","entry":[{"id":"1056","changes":[{"value":{'
        '"messaging_product":"whatsapp","metadata":{"display_phone_number":"1555","phone_number_id":"1085"},'
        '"contacts":[{"profile":{"name":"Test User"},"wa_id":"9715"}],"messages":[{"context":{'
        '"forwarded":true},"from":"9715","id":"wamid.HBgM=","timestamp":"1686277037","type":"video",'
        '"video":{"mime_type":"video\\/mp4","sha256":"vZjyK=","id":"2295"}}]},'
        '"field":"messages"}]}]}',
    }


def test_verify(message_verify, message_read, message_text):
    challenge = wa.verify_whatsapp_webhook(message_verify)
    assert challenge == "73736871"

    assert wa.verify_whatsapp_webhook(message_read) is None
    assert wa.verify_whatsapp_webhook(message_text) is None


def test_message(message_text, message_read, message_media_image):
    msg = wa.read_text_message(json.loads(message_text["body"]))
    assert msg.from_phone == "9715"
    assert msg.text == "hello world"

    msg = wa.read_text_message(json.loads(message_read["body"]))
    assert msg is None

    msg = wa.read_text_message(json.loads(message_media_image["body"]))
    assert msg is None


def test_message_read(message_read, message_text):
    msg = wa.message_was_read(json.loads(message_read["body"]))
    assert msg.status == "read"
    assert msg.recipient == "9715"

    msg = wa.message_was_read(json.loads(message_text["body"]))
    assert msg is None


def test_media_message(message_media_image, message_media_video, message_text):
    msg = wa.read_media_message(json.loads(message_media_image["body"]))
    assert msg.from_phone == "9715"
    assert msg.media_id == "2295"
    assert msg.mime_type == "image/jpeg"
    assert msg.text == "15 days order"

    msg = wa.read_media_message(json.loads(message_media_video["body"]))
    assert msg.from_phone == "9715"
    assert msg.media_id == "2295"
    assert msg.mime_type == "video/mp4"
    assert not msg.text

    msg = wa.read_media_message(json.loads(message_text["body"]))
    assert msg is None


def _load_json(file: Path) -> dict:
    with open(file) as f:
        return json.load(f)
