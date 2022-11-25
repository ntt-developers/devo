import requests
import os
import json
import psycopg2
import time

bearer_token = os.environ.get("BEARER_TOKEN")

def select_url(url):
    dsn = os.environ.get("PSQL_DSN_DOG")
    sql = "select count(*) from twurl where tweeturl = %s"

    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql,(url,))
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
    ret = {"tweet.fields": "created_at","exclude":"retweets,replies","max_results":10}
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
    url = create_url()
    ids = []
    # connect to Twitter API
    params = get_params("")
    response = connect_to_endpoint(url, params)
    result = response['data']
        
    # compare URLs
    for res in result:
        url = "https://twitter.com/jikkainu/status/"+res['id']
        db_url = select_url(url)
        if db_url == 0:
            ids.append(url)

    # new Tweet -> insertDB, slackPost
    if len(ids) != 0:
        insert_url(reversed(ids))
        for url in reversed(ids):
            message = title_message
            message += url
            slack_post_message(message,dog_channel)
            if len(ids) != 1:
                time.sleep(1)

if __name__ == "__main__":
    main()
