import requests
import os
import json
import psycopg2
import time

bearer_token = os.environ.get("BEARER_TOKEN")

def select_latest():
    dsn = os.environ.get("PSQL_DSN_DOG")
    sql = "select tweeturl from twurl where index = (select max(index) from twurl)"

    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            results = cur.fetchall()
    return results[0][0]

def insert_url(result):
    dsn = os.environ.get("PSQL_DSN_DOG")
    
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            for res in result:
                cur.execute('INSERT INTO twurl (tweeturl) VALUES (%s)', (res,))
        conn.commit()


def create_url():
    user_id = 1289855022264541184
    return "https://api.twitter.com/2/users/{}/tweets".format(user_id)


def get_params(token):
    ret = {"tweet.fields": "created_at","exclude":"retweets,replies"}
    if token:
        ret["pagination_token"] = token

    return ret


def bearer_oauth(r):
    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2UserTweetsPython"
    return r


def connect_to_endpoint(url, params):
    response = requests.request("GET", url, auth=bearer_oauth, params=params)
    #print(response.status_code)
    if response.status_code != 200:
        raise Exception(
            "Request returned an error: {} {}".format(
                response.status_code, response.text
            )
        )
    return response.json()

def slack_post_message(message,channel):
    url = "https://slack.com/api/chat.postMessage"
    token = os.environ["SLACK_BOT_TOKEN_DEVO"]

    payload = {"token":token,
            "channel":channel,
            "text":message
    }

    requests.post(url,data=payload)

def main():
    dog_channel = os.environ["DOG_CHANNEL_ID"]
    title_message = "New Tweet in 実家のいぬ\n"
    latest_url = select_latest()
    url = create_url()
    ids = []
    has_next = True
    c = 0
    max_c = 3
    next_token = ""
    while has_next:
        # connect to Twitter API
        params = get_params(next_token)
        response = connect_to_endpoint(url, params)
        result = response['data']
        
        has_next = ('next_token' in response['meta'] and c < max_c)
        if has_next:
            next_token = response['meta']['next_token']

        # compare latestURL
        for res in result:
            url = "https://twitter.com/jikkainu/status/"+res['id']
            if latest_url == url:
                has_next = False
                break
            else:
                ids.append(url)

        # new Tweet -> insertDB, slackPost
        if len(ids) != 0:
            insert_url(ids)
            for url in ids:
                message = title_message
                message += url
                slack_post_message(message,dog_channel)
                if len(ids) != 1:
                    time.sleep(1)
        ids.clear()
        c += 1
        time.sleep(1)

if __name__ == "__main__":
    main()
