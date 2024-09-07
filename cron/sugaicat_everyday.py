import os
import datetime
import requests
import sys
import json
sys.path.append('..')

from mugiRand import mugiRandClass as mugi

def slack_post_file(message,channel,filepath,filename,title):

    token = os.environ["SLACK_BOT_TOKEN_DEVO"]
    filesize = os.path.getsize(filepath)

    # 1.getUploadURLExternal API
    getUpUrl = "https://slack.com/api/files.getUploadURLExternal"
    head_token = "Bearer " + token
    headers_1 = {"Authorization":head_token}
    payload_1 = {
            "filename":filename,
            "length":filesize
    }
    ret_1 = requests.get(getUpUrl,params=payload_1,headers=headers_1)
    ret_1_json = ret_1.json()

    #print(ret_1_json)

    if ret_1_json.get("ok") == False:
        print(ret_1.get("error"))
        return

    # 2. file UPLOAD at POST
    fileUpUrl = ret_1_json.get("upload_url")
    file_id = ret_1_json.get("file_id")
    files = {'file': open(filepath, 'rb')}

    ret_2 = requests.post(fileUpUrl, files=files)

    #print(ret_2.content)

    # 3. file Complete API
    fileCompUrl = "https://slack.com/api/files.completeUploadExternal"
    files_str = "[{\"id\":\"" + file_id + "\",\"title\":\"" + title + "\"}]"

    payload_3 = {"token":token,
            "files":files_str,
            "channel_id":channel,
            "initial_comment":message
    }

    ret_3 = requests.post(fileCompUrl,data=payload_3)

    #print(ret_3.content)

# --- Main ---

mg = mugi.mugiRandClass()
filepath = mg.get_file()
filename = mg.filename

cat_channel = os.environ["CAT_CHANNEL_ID"]

message = "Today's :sugaicat:\n"
title = "撮影日：" + mg.createDate.strftime('%Y-%m-%d')
slack_post_file(message,cat_channel,filepath,filename,title)

mg.delete_tmp_file()
