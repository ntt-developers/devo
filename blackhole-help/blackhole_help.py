import os
import requests
import datetime
import time
import psycopg2

token = os.environ.get("SLACK_USER_TOKEN")
bl_ch_id = os.environ.get("BL_CHANNEL_ID")
dsn = os.environ.get("BL_LOG_DSN")

def slack_search():
    url = "https://slack.com/api/search.messages"
    params = {
            "query":"in:#blackhole",
            "count":"100"
    }
    headers = { 'Authorization': 'Bearer ' + token}
    response = requests.get(url, headers=headers, params=params)
    #print(response.status_code)
    #print(response.content)
    return response.json()


def slack_delete_post(main_ts):
    url = "https://slack.com/api/chat.delete"
    payload = {"token":token,
            "channel":bl_ch_id,
            "ts":main_ts
    }

    response = requests.post(url,data=payload)
    #print(response.status_code)
    #print(response.content)

def insert_log(ts,post_at,user_id,text):
    sql = "insert into bl_log(ts,post_at,user_id,text) values(%s,%s,%s,%s)"
    with psycopg2.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(sql,(ts,post_at,user_id,text))

def main():
    ret_json = slack_search()

    matches = ret_json.get("messages").get("matches")
    for mat in matches:
        main_ts = mat.get("ts")
        main_unix = int(main_ts.split('.')[0])
        main_time = datetime.datetime.fromtimestamp(main_unix)
        if(datetime.datetime.now() - datetime.timedelta(hours=1,minutes=3) > main_time):
            user_id = mat.get("user")
            text = mat.get("text")
            insert_log(main_ts,main_time,user_id,text)
            slack_delete_post(main_ts)
            time.sleep(2)

# app start
if __name__ == "__main__":
    main()
