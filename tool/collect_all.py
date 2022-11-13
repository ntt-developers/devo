import requests
import os
import json
import psycopg2
import time

bearer_token = os.environ.get("BEARER_TOKEN")

def insert_url(result):
    dsn = os.environ.get("PSQL_DSN_DOG")
    
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            for res in result:
                cur.execute('INSERT INTO collect (tweeturl) VALUES (%s)', (res,))
        conn.commit()


def create_url():
    user_id = 1289855022264541184
    return "https://api.twitter.com/2/users/{}/tweets".format(user_id)


def get_params(token):
    ret = {"tweet.fields": "created_at","exclude":"retweets"}
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


def main():
    url = create_url()
    ids = []
    has_next = True
    c = 0
    next_token = ""
    while has_next:
        print("c:"+str(c))

        # connect to Twitter API
        params = get_params(next_token)
        response = connect_to_endpoint(url, params)
        result = response['data']
        
        has_next = ('next_token' in response['meta'] and c < 400)
        if has_next:
            next_token = response['meta']['next_token']

        for res in result:
           ids.append("https://twitter.com/jikkainu/status/"+res['id'])
        insert_url(ids)
        ids.clear()
        c = c + 1
        time.sleep(1)

    #print(json.dumps(response, indent=4, sort_keys=True))

if __name__ == "__main__":
    main()
