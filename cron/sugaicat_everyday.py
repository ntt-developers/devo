import os
import datetime
import requests
import sys
sys.path.append('..')

from mugiRand import mugiRandClass as mugi

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

mg = mugi.mugiRandClass()
filepath = mg.get_file()

cat_channel = os.environ["CAT_CHANNEL_ID"]

message = "Today's :sugaicat:\n"
title = datetime.datetime.now().strftime('%Y-%m-%d')
slack_post_file(message,cat_channel,filepath,title)

mg.delete_tmp_file()
