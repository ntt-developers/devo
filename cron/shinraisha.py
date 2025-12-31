import os
import requests
import datetime
import json
import psycopg2

def slack_post_message(blocks,channel):
    url = "https://slack.com/api/chat.postMessage"
    token = os.environ["SLACK_BOT_TOKEN_DEVO"]
    
    payload = {"token":token,
            "channel":channel,
            "blocks":blocks
    }

    requests.post(url,data=payload)

# true->holiday, false->weekday
def dateCheck():
    dsn = os.environ.get("PSQL_DSN_DEVO")
    sql = "select date_str from shukujitsu"
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            results = cur.fetchall()

    str_today = datetime.date.today().strftime("%Y%m%d")
    for res in results:
        if res[0] == str_today:
            return True
    
    wd = datetime.datetime.now().weekday()
    if wd == 5 or wd == 6:
        return True

    return False

# --- Main ---
def main():
    if not dateCheck():
        return

    post_channel = os.environ["BL_CHANNEL_ID"]

#    blo = '[{"text": {"type": "mrkdwn","text": "*おはようございます！* :shinraisha: になりますか？"},"type": "section"},{"type": "divider"},{"elements": [{"text": {"type": "plain_text","text": "起床する"},"action_id": "shinraisha","type": "button"}],"type": "actions"}]'
    blo = '[{"text": {"type": "mrkdwn","text": "*おはようございます！* :shinraisha: になりますか？"},"type": "section"},{"type": "divider"},{"elements": [{"text": {"type": "plain_text","text": "起床する"},"action_id": "shinraisha","type": "button"}],"type": "actions"},{"type": "divider"},{"type": "actions","elements": [{"type": "button","text": {"type": "plain_text","text": "ランキングを見る"},"action_id": "shinrai-rank"}]},{"type": "actions","elements": [{"type": "button","text": {"type": "plain_text","text": "これは何？"},"action_id": "shinrai-help"}]}]'

    slack_post_message(blo,post_channel)

# app start
if __name__ == "__main__":
    main()
