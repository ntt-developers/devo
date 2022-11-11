import os
import psycopg2
import requests
import json

def select_random_url():
    dsn = os.environ.get("PSQL_DSN_DOG")
    sql = "SELECT * FROM twurl WHERE index=(SELECT (max(index) * random())::int FROM twurl)"

    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            results = cur.fetchall()
    return results[0][1]

def slack_post_message(message,channel):
    url = "https://slack.com/api/chat.postMessage"
    token = os.environ["SLACK_BOT_TOKEN_DEVO"]
    
    payload = {"token":token,
            "channel":channel,
            "text":message
    }

    requests.post(url,data=payload)

# --- Main ---

url = select_random_url()
dog_channel = os.environ["DOG_CHANNEL_ID"]

message = "Today's 実家のいぬ\n"
message += url

slack_post_message(message,dog_channel)
