import os
import psycopg2
from psycopg2  import extras
import requests
import datetime
import json

def select_inviter_over():
    dsn = os.environ.get("PSQL_DSN_DEVO")
    sql = "select seq, guest_user_id, inviter_user_id, created_at from inviter where delete_flag is false and created_at < (now() + '-1 month') and notice is false order by created_at asc"

    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            results = cur.fetchall()
    return results

def update_notice_flag(upd_list):
    dsn = os.environ.get("PSQL_DSN_DEVO")
    sql = "update inviter set notice = true where seq in %s"

    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            extras.execute_values(cur, sql, [upd_list])
            conn.commit()

def slack_post_message(message,channel):
    url = "https://slack.com/api/chat.postMessage"
    token = os.environ["SLACK_BOT_TOKEN_DEVO"]
    
    payload = {"token":token,
            "channel":channel,
            "text":message
    }

    requests.post(url,data=payload)

def slack_get_users_info(user_id):
    url = "https://slack.com/api/users.info"
    token = os.environ["SLACK_BOT_TOKEN_DEVO"]

    head_token = "Bearer " + token
    headers = {"Authorization":head_token}

    payload = {
            "user":user_id
    }
    ret = requests.get(url,params=payload,headers=headers)
    return ret.json()

def slack_get_users_email(user_id):
    if user_id is None:
        return "No Data"

    ret = slack_get_users_info(user_id)

    email = ret.get("user").get("profile").get("email")
    if email is None:
        email = "No Data"

    return email

def slack_get_users_name(user_id):
    if user_id is None:
        return "No Data"
    
    ret = slack_get_users_info(user_id)

    name = ret.get("user").get("profile").get("display_name")
    if name is None:
        name = "No Data"

    return name

# --- Main ---
def main():
    post_channel = os.environ["ADMIN_CHANNEL_ID"]
    data = select_inviter_over()
    if data == []:
        return

    update_list = []
    message = "1ヶ月以上放置された招待リストがあります\n\n"
    for dat in data:
        message += "("
        message += str(dat[0])
        message += ") *"
        message += slack_get_users_email(dat[1])
        message += "*\n"
        message += "        招待者："
        message += slack_get_users_name(dat[2])
        message += "\n"
        message += "        招待日時："
        message += dat[3].strftime('%Y-%m-%d')
        message += "\n"

        update_list.append(str(dat[0]))

    message += "\n※devo情報なので実際のWS管理画面と異なる場合があります\n"
    message += "<@UC1HYS54Y> はdevo情報をWS管理画面と同期させてね <https://ntt-developers.slack.com/admin/invites|招待リスト>\n"
    slack_post_message(message,post_channel)
    update_notice_flag(update_list)

# app start
if __name__ == "__main__":
    main()
