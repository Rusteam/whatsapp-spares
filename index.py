import json
import os

import cv2
from heyoo import WhatsApp

from bot import parse, utils, wa
from bot.log import setup_logger
from bot.workers import ScreenshotQuoteParser

logger = setup_logger("handler")

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
HEADER_TOKEN = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
HEADER_JSON = {"Content-Type": "application/json"}

img_processor = ScreenshotQuoteParser()
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


def _handle_media_message(msg: wa.MediaMessage) -> dict:
    try:
        # media_url = wa.retrieve_media_url(msg.media_id, HEADER_TOKEN)
        # img = utils.download_image(media_url, headers=HEADER_TOKEN)
        media_url = messenger.query_media_url(msg.media_id)
        img_file = messenger.download_media(media_url, msg.mime_type)
        img = cv2.imread(img_file)[:, :, ::-1]  # pylint: disable=no-member
        res = img_processor.execute(img)
        text = "\n\n".join([str(out) for out in res])

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
            return _handle_media_message(msg)
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
