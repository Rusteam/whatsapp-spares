import json
import os

import cv2
from heyoo import WhatsApp

from bot import wa
from bot.log import setup_logger
from bot.utils import parse

logger = setup_logger("handler")

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
HEADER_TOKEN = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
HEADER_JSON = {"Content-Type": "application/json"}

messenger = WhatsApp(WHATSAPP_TOKEN)


def _format_final_response(resp, text, phone_number: str):
    if resp is not None:
        logger.info(
            f"sent message",
            extra={
                "status_code": resp.status_code,
                "body": text,
                "phone_id": phone_number,
            },
        )
        return {
            "statusCode": resp.status_code,
            "body": resp.content.decode(),
        }
    else:
        logger.error("ERROR: no response from send_retry")
        return {
            "statusCode": 500,
            "body": "ERROR: no response from send_retry",
        }


def _handle_text_message(msg: wa.TextMessage) -> dict:
    try:
        output_data = parse.process_message(msg.text)
        text = "\n\n".join([out.format() for out in output_data])

    except Exception as e:
        logger.error("ERROR in handler", exc_info=e)
        text = f"ERROR: {e}"

    resp = wa.send_retry(text, msg.from_phone, HEADER_TOKEN | HEADER_JSON, max_retry=10)
    return _format_final_response(resp, text, msg.from_phone)


def handler(event, context):
    logger.info(f"EVENT: {event}")

    if challenge := wa.verify_whatsapp_webhook(event):
        logger.info("webhook has been verified", extra={"challenge": challenge})
        return {
            "statusCode": 200,
            "body": challenge,
        }
    else:
        body = json.loads(event["body"])

        if msg := wa.read_text_message(body):
            return _handle_text_message(msg)
        elif msg := wa.read_media_message(body):
            raise NotImplementedError("media is not implemented yet.")
        elif msg := wa.message_was_read(body):
            logger.info("message was read", extra=msg.dict())
            return {
                "statusCode": 200,
                "body": "OK",
            }
        else:
            logger.error("unknown event", extra={"body": body})
            return {
                "statusCode": 403,
                "body": "unknown event",
            }
