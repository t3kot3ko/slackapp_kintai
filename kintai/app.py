import boto3
import json
import logging
import urllib.request
import os
import re

from botocore.config import Config

logger = logging.getLogger()
logger.setLevel(logging.INFO)

config = Config(proxies={'https': os.getenv("HTTPS_PROXY")}) if os.getenv("HTTPS_PROXY") else None
ddb = boto3.resource("dynamodb", config=config)

table = ddb.Table(os.getenv("TABLE_NAME"))  # Passed from template.yaml

def lambda_handler(event, context):
    # TODO implement
    body = json.loads(event["body"])
    
    logging.info(body)

    # Challenge
    if "challenge" in body.keys():
        return {
            'statusCode': 200,
            "headers": {},
            'body': body["challenge"]
        }
        
    # TODO: Token validation
    token = body["token"]

    if token != os.getenv("SLACK_VERIFICATION_TOKEN"):
        return {
            'statusCode': 500,
            "headers": {},
            'body': {"text": "Could not validate the request (token did not match)"}
        }

    if body["event"]["type"] == "app_mention":
        event_str = "```\n" + str(event) + "\n```"

        event_id = body["event_id"]
        event_time = body["event_time"]

        text = body["event"]["text"].replace("@kintai ", "")
        user_id = body["event"]["user"]
        timestamp = body["event"]["ts"]

        logging.info("Trying to put_item")
        table.put_item(Item={
            "event_id": event_id, 
            "user_id": user_id, 
            "text": text,
            "timestamp": timestamp,
            })
        return __response_200("Successfully inserted")


    return __response_500("Unsupported event type")

def __response_200(text):
    return {
        'statusCode': 200,
        "headers": {},
        'body': {"text": text}
    }

def __response_500(text):
    return {
        'statusCode': 500,
        "headers": {},
        'body': {"text": text}
    }

def __post_text(incomming_webhook_url, text):
    data = json.dumps({"text": text}).encode("utf-8")
    headers = {"Content-Type" : "application/json"}
    request = urllib.request.Request(incomming_webhook_url, data, method="POST", headers=headers)

    # For debug purpose
    if os.getenv("HTTPS_PROXY"):
        request.set_proxy(os.getenv("HTTPS_PROXY"), "https")
    
    with urllib.request.urlopen(request) as response:
        response_body = response.read().decode("utf-8")
            
    return __response_200(response_body)
