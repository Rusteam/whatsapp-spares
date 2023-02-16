import json
import os

from bot import parse, wa

TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}


def handler(event, context):
    print("EVENT", event)

    if challenge := wa.verify_whatsapp_webhook(event):
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
                print("ERROR in handler", e)
                text = f"ERROR: {e}"

            print(f"SENDING to {msg.from_phone}:", text)

            resp = wa.send_retry(text, msg.from_phone, HEADERS, max_retry=10)
            if resp:
                return {
                    "statusCode": resp.status_code,
                    "body": resp.content.decode(),
                }
            else:
                return {
                    "statusCode": 500,
                    "body": "ERROR: no response from send_retry",
                }
        msg = wa.message_was_read(body)
        # TODO log this
        if msg:
            return {
                "statusCode": 200,
                "body": "OK",
            }

        return {
            "statusCode": 403,
            "body": "unknown event",
        }
