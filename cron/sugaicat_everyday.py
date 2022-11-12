import os
import requests
import json
import random

def select_random_url():
    path = "../sugaicat.txt"
    with open(path) as f:
        lines = f.readlines()

    rand_max = 797
    return lines[random.randint(0,rand_max-1)]

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
cat_channel = os.environ["CAT_CHANNEL_ID"]

message = "Today's :sugaicat:\n"
message += url

slack_post_message(message,cat_channel)
