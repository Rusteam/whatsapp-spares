import time
from typing import Optional

import requests
from pydantic import BaseModel  # pylint: disable=no-name-in-module

URL = "https://graph.facebook.com/v16.0/{PHONE_ID}/messages"


class TextMessage(BaseModel):
    from_phone: str
    text: str


class MessageStatus(BaseModel):
    status: str
    recipient: str


def verify_whatsapp_webhook(event: dict) -> Optional[str]:
    """Verify the webhook subscription."""
    mode = event["queryStringParameters"].get("hub.mode")
    challenge = event["queryStringParameters"].get("hub.challenge")
    token = event["queryStringParameters"].get("hub.verify_token")

    if mode and token:
        if mode == "subscribe" and token == "HAPPY_CODING":
            return challenge
    return None


def read_text_message(event_body: dict) -> TextMessage:
    changes = event_body["entry"][0]["changes"][0]["value"]
    if "messages" in changes:
        from_phone = changes["messages"][0]["from"]
        input_text = changes["messages"][0]["text"]["body"]
        return TextMessage(from_phone=from_phone, text=input_text)
    else:
        return None


def message_was_read(event_body: dict) -> MessageStatus:
    changes = event_body["entry"][0]["changes"][0]["value"]
    if "statuses" in changes:
        return MessageStatus(
            status=changes["statuses"][0]["status"],
            recipient=changes["statuses"][0]["recipient_id"],
        )
    else:
        return None


def send_retry(text, phone_id: str, headers: dict, max_retry: int = 10):
    i = 0
    url = URL.format(PHONE_ID=phone_id)
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone_id,
        "type": "text",
        "text": {"preview_url": False, "body": text},
    }
    while i < max_retry:
        try:
            resp = requests.post(
                url, headers=headers, json=payload, verify=False, timeout=60
            )
            return resp
        except Exception as e:
            print("ERROR in handler", e)
            time.sleep(1)
            i += 1
            continue
