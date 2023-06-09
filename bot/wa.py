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


class MediaMessage(TextMessage):
    media_id: str
    mime_type: str


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


def _get_last_change(event_body: dict) -> dict:
    return event_body["entry"][0]["changes"][0]["value"]


def _get_phone_number(changes: list) -> str:
    from_phone = changes["messages"][0]["from"]
    if from_phone.startswith("7"):
        from_phone = "78" + from_phone[1:]
    return from_phone


def read_text_message(event_body: dict) -> TextMessage:
    changes = _get_last_change(event_body)
    if "messages" in changes and changes["messages"][0]["type"] == "text":
        from_phone = _get_phone_number(changes)
        input_text = changes["messages"][0]["text"]["body"]
        logger.debug(f"received message: {input_text}", extra={"from": from_phone})
        return TextMessage(from_phone=from_phone, text=input_text)
    else:
        return None


def message_was_read(event_body: dict) -> MessageStatus:
    changes = _get_last_change(event_body)
    if "statuses" in changes:
        msg = MessageStatus(
            status=changes["statuses"][0]["status"],
            recipient=changes["statuses"][0]["recipient_id"],
        )
        return msg
    else:
        return None


def read_media_message(event_body: dict) -> MediaMessage:
    changes = _get_last_change(event_body)
    if "messages" in changes and changes["messages"][0]["type"] in ["image", "video"]:
        phone_number = _get_phone_number(changes)
        media_type = changes["messages"][0]["type"]
        media_content = changes["messages"][0][media_type]
        logger.debug(f"received media: {media_content}", extra={"from": phone_number})
        return MediaMessage(
            text=media_content.get("caption", ""),
            media_id=media_content["id"],
            mime_type=media_content["mime_type"],
            from_phone=phone_number,
        )
    else:
        return None


def retrieve_media_url(media_id: str, headers: dict) -> str:
    """Retrieve media url from cloud api."""
    resp = requests.get(
        f"https://graph.facebook.com/v16.0/{media_id}",
        headers=headers,
        verify=False,
        timeout=60,
    )
    logger.debug(
        "GET media url",
        extra={
            "status_code": resp.status_code,
            "content": resp.content.decode(),
        },
    )
    if resp.status_code == 200:
        return resp.json()["url"]
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
