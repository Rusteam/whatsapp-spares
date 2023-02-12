import json
import os
import time

import requests

from bot import parse

TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
URL = f"https://graph.facebook.com/v16.0/{PHONE_ID}/messages"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}


def handler(event, context):
    print("EVENT", event)

    mode = event["queryStringParameters"].get("hub.mode")
    challenge = event["queryStringParameters"].get("hub.challenge")
    token = event["queryStringParameters"].get("hub.verify_token")

    if mode and token:
        if mode == "subscribe" and token == "HAPPY_CODING":
            print("ok", challenge)
            return {
                "statusCode": 200,
                "body": challenge,
            }
    else:
        body = json.loads(event["body"])
        changes = body["entry"][0]["changes"][0]["value"]
        from_phone = changes["contacts"][0]["wa_id"]

        try:
            input_text = changes["messages"][0]["text"]["body"]
            output_data = parse.process_message(input_text)
            text = "\n\n".join([out.format() for out in output_data])

        except Exception as e:
            print("ERROR in handler", e)
            text = f"ERROR: {e}"

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": from_phone,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }

        print(f"SENDING to {from_phone}:", text)

        i = 0
        while i < 3:
            try:
                resp = requests.post(
                    URL, headers=HEADERS, json=payload, verify=False, timeout=60
                )
                break
            except Exception as e:
                print("ERROR in handler", e)
                time.sleep(1)
                i += 1
                continue

        return {
            "statusCode": resp.status_code,
            "body": resp.content.decode(),
        }

    return {
        "statusCode": 403,
        "body": "mode or challenge incorrect",
    }
