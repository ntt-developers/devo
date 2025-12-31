import os
import requests
import datetime
import json
import psycopg2
import time

def slack_post_message_main(message):
    url = "https://slack.com/api/chat.postMessage"
    token = os.environ["SLACK_BOT_TOKEN"]
    channel = os.environ["POST_CHANNEL_ID"]

    payload = {"token":token,
            "channel":channel,
            "text":message
    }

    ret = requests.post(url,data=payload)
    ret_json = ret.json()
    return ret_json.get("message").get("ts")

def slack_post_message_thread(message,ts):
    url = "https://slack.com/api/chat.postMessage"
    token = os.environ["SLACK_BOT_TOKEN"]
    channel = os.environ["POST_CHANNEL_ID"]

    payload = {"token":token,
            "channel":channel,
            "text":message,
            "thread_ts":ts
    }
    requests.post(url,data=payload)

def slack_get_user_info(user_id):
    url = "https://slack.com/api/users.profile.get"
    token = os.environ["SLACK_BOT_TOKEN"]

    head_token = "Bearer " + token
    headers = {"Authorization":head_token}

    payload = {
            "user":user_id
    }
    ret = requests.get(url,params=payload,headers=headers)
    return ret.json()

def get_ranking_db():
    dsn = os.environ["PSQL_DSN"]
    sql = "SELECT user_id,count(user_id),rank() OVER (ORDER BY count(user_id) desc) FROM shinrai GROUP BY user_id ORDER BY count(user_id) DESC"
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            results = cur.fetchall()
    return results

# --- Main ---
def main():

    fir_message = "あけましておめでとうございます。2025年の :shinraisha: TOP30を発表します。\n※試験的投稿のため三が日とも同じ内容をポストします。"
    ts = slack_post_message_main(fir_message)
    rank_data = get_ranking_db()

    rank_message = ""
    now_rank = 0
    i = 0
    while(now_rank < 30):
        line_message = ""
        now_rank = rank_data[i][2]
        user_id = rank_data[i][0]
        cnt = rank_data[i][1]
        
        time.sleep(0.1)
        user_profile = slack_get_user_info(user_id).get("profile")
        if user_profile is None:
            user_name = "[deactivated user]"
        else:
            user_name = user_profile.get("display_name")

        line_message += str(now_rank)
        line_message += "位："
        line_message += user_name
        line_message += " ("
        line_message += str(cnt)
        line_message += "回)\n"
        rank_message = rank_message + line_message
        i = i+1

    slack_post_message_thread(rank_message,ts)


# app start
if __name__ == "__main__":
    main()
