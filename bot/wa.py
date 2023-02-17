import os
import time
from typing import Optional

import requests
from pydantic import BaseModel  # pylint: disable=no-name-in-module

from bot.log import setup_logger

logger = setup_logger("whatsapp")

PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
URL = f"https://graph.facebook.com/v16.0/{PHONE_ID}/messages"


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
        if from_phone.startswith("7"):
            from_phone = "78" + from_phone[1:]
        input_text = changes["messages"][0]["text"]["body"]
        logger.debug("received message", extra={"from": from_phone, "text": input_text})
        return TextMessage(from_phone=from_phone, text=input_text)
    else:
        return None


def message_was_read(event_body: dict) -> MessageStatus:
    changes = event_body["entry"][0]["changes"][0]["value"]
    if "statuses" in changes:
        msg = MessageStatus(
            status=changes["statuses"][0]["status"],
            recipient=changes["statuses"][0]["recipient_id"],
        )
        return msg
    else:
        return None


def send_retry(text, phone_id: str, headers: dict, max_retry: int = 10):
    i = 0
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
                URL, headers=headers, json=payload, verify=False, timeout=60
            )
            logger.debug(
                "POST message",
                extra={
                    "status_code": resp.status_code,
                    "body": text,
                    "phone_id": phone_id,
                    "content": resp.content.decode(),
                },
            )
            return resp
        except Exception as e:
            logger.warn("error sending message", exc_info=e, extra={"retry": i})
            time.sleep(1)
            i += 1
