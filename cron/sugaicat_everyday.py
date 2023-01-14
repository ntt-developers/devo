import os
import requests
import json
import random
import datetime

def select_random_file():
    path = os.environ["SUGAICAT_PATH"]
    files = os.listdir(path)
    files_file = [f for f in files if os.path.isfile(os.path.join(path, f))]
    fileone = random.choice(files_file)
    return os.path.join(path, fileone)

def slack_post_file(message,channel,filepath,title):
    url = "https://slack.com/api/files.upload"
    token = os.environ["SLACK_BOT_TOKEN_DEVO"]
    files = {'file': open(filepath, 'rb')}
    filename = os.path.basename(filepath)
    payload = {"token":token,
            "channels":channel,
            "initial_comment":message,
            "filename":filename,
            "title":title
    }
    response = requests.post(url, files=files, data=payload)
    #print(response.status_code)
    #print(response.content)
# --- Main ---

filepath = select_random_file()
cat_channel = os.environ["CAT_CHANNEL_ID"]

message = "Today's :sugaicat:\n"
title = datetime.datetime.now().strftime('%Y-%m-%d')
slack_post_file(message,cat_channel,filepath,title)
