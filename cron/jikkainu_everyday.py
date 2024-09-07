import os
import psycopg2
import requests
import json

def select_random():
    dsn = os.environ.get("PSQL_DSN_DOG")
    sql = "select id, text from tweet order by random() limit 1"

    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            results = cur.fetchall()
    return results

def slack_post_message(message,channel):
    url = "https://slack.com/api/chat.postMessage"
    token = os.environ["SLACK_BOT_TOKEN_DEVO"]
    
    payload = {"token":token,
            "channel":channel,
            "text":message
    }

    requests.post(url,data=payload)

# --- Main ---

data = select_random()
dog_channel = os.environ["DOG_CHANNEL_ID"]
tid = data[0][0]
url = "https://fxtwitter.com/jikkainu/status/" + tid

text = data[0][1]

message = "Today's 実家のいぬ\n"
message += "\n"
message += text
message += "\n"
message += url

slack_post_message(message,dog_channel)
