import json
import os

from bot import parse, wa
from bot.log import setup_logger

logger = setup_logger("handler")

TOKEN = os.getenv("WHATSAPP_TOKEN")
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}


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

        msg = wa.read_text_message(body)
        if msg:
            try:
                output_data = parse.process_message(msg.text)
                text = "\n\n".join([out.format() for out in output_data])

            except Exception as e:
                logger.error("ERROR in handler", exc_info=e)
                text = f"ERROR: {e}"

            resp = wa.send_retry(text, msg.from_phone, HEADERS, max_retry=10)
            if resp is not None:
                logger.info(
                    f"sent message",
                    extra={
                        "status_code": resp.status_code,
                        "body": text,
                        "phone_id": msg.from_phone,
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
        msg = wa.message_was_read(body)
        if msg:
            logger.info("message was read", extra=msg.dict())
            return {
                "statusCode": 200,
                "body": "OK",
            }

        logger.error("unknown event", extra={"body": body})
        return {
            "statusCode": 403,
            "body": "unknown event",
        }
