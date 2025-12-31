import os
import logging
import re
import random
import psycopg2
import datetime
import json
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from time import sleep
from googleapiclient.discovery import build
from mugiRand import mugiRandClass as mugi

# app init
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

# log level
if os.environ.get("LOG_LEVEL") == "INFO":
    logging.basicConfig(level=logging.INFO)
elif os.environ.get("LOG_LEVEL") == "DEBUG":
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

# ---common function---

def file_read(filename):
    f = open(filename,'r')
    data = f.read()
    f.close()
    return data

def create_intro_message(joinUserName,inviteUserName):

    filetext = file_read("intro_message.txt") 

    introductions_channel_id = os.environ.get("INTRODUCTIONS_CHANNEL_ID")
    timeline_channel_id = os.environ.get("TIMELINE_CHANNEL_ID")
    message = filetext.format(joinUserName,introductions_channel_id,timeline_channel_id,inviteUserName)

    return message

def select_random_jikkainu():
    dsn = os.environ.get("PSQL_DSN_DOG")
    sql = "select id, text from tweet order by random() limit 1"
    
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            results = cur.fetchall()
    return results

def select_sugaicat_file():
    path = os.environ["SUGAICAT_PATH"]
    files = os.listdir(path)
    files_file = [f for f in files if os.path.isfile(os.path.join(path, f))]
    fileone = random.choice(files_file)
    return os.path.join(path, fileone)

def get_search_img(keyword):
    today = datetime.datetime.today().strftime("%Y%m%d")
    timestamp = datetime.datetime.today().strftime("%Y-%m-%d_%H-%M-%S")
    json_dir = os.environ.get("JSON_DIR")
    g_api_key = os.environ.get("GOOGLE_API_KEY")
    cse_id = os.environ.get("CUSTOM_SEARCH_ENGINE_ID")

    if not os.path.isdir(json_dir):
        os.mkdir(json_dir)

    service = build("customsearch", "v1", developerKey=g_api_key, cache_discovery=False)

    page_limit = 2
    start_index = 1
    response = []
    for n_page in range(0, page_limit):
        try:
            sleep(1)
            response.append(service.cse().list(
                q=keyword,
                cx=cse_id,
                lr='lang_ja',
                num=10,
                start=start_index,
                searchType='image'
            ).execute())
            start_index = response[n_page].get("queries").get("nextPage")[0].get("startIndex")
        except Exception as e:
            logging.error(e)
            break

    out = {'snapshot_ymd': today, 'snapshot_timestamp': timestamp, 'response': []}
    out['response'] = response
    filename = os.path.join(json_dir, today + "_" + timestamp + '.json')
    with open(filename,'w') as f:
        json.dump(out, f, indent=4)

    img_list = []
    for one_res in range(len(response)):
        if len(response[one_res]['items']) > 0:
            for i in range(len(response[one_res]['items'])):
                tmp_dic = {
                        "title":response[one_res]['items'][i]['title'],
                        "link":response[one_res]['items'][i]['link'],
                        "thmb":response[one_res]['items'][i]['image']['thumbnailLink']
                }
                img_list.append(tmp_dic)

    # insert log
    dsn = os.environ.get("PSQL_DSN_DEVO")
    sql_head = "INSERT INTO gimglog_head(terms) VALUES (%s) RETURNING id"
    sql_item = "INSERT INTO gimglog_item(id,count,title,link,thumb) VALUES(%s,%s,%s,%s,%s)"

    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql_head,(keyword,))
            
            db_id = cur.fetchone()[0]
            db_count = 0
            for lis in img_list:
                db_count += 1
                cur.execute(sql_item,(db_id,
                                    db_count,
                                    lis.get("title"),
                                    lis.get("link"),
                                    lis.get("thmb"),))
    
    return img_list

# ---event function---

@app.event("member_joined_channel")
def check_inviter(body, logger, say):
    logger.debug(body)

    general_channel_id = os.environ.get("SLACK_GENERAL_CHANNEL_ID")

    # join to general channel -> new person join
    if body['event']['channel'] == general_channel_id:
        guestUser = body['event']['user']

        # in some cases, 'inviter' is null
        if 'inviter' in body['event']:
            inviteUser = body['event']['inviter']
        else:
            inviteUser = None

        dsn = os.environ.get("PSQL_DSN_DEVO")
        sql = "INSERT INTO inviter (guest_user_id,inviter_user_id) VALUES (%s,%s)"

        with psycopg2.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(sql,(guestUser,inviteUser))

@app.event({
    "type": "message",
    "subtype": "channel_join"
})
def ask_for_introduction(body, logger, say):
    logger.debug(body)

    general_channel_id = os.environ.get("SLACK_GENERAL_CHANNEL_ID")

    # join to general channel -> new person join
    if body['event']['channel'] == general_channel_id:
        joinUser = body['event']['user']

        # search inviter user in DB
        dsn = os.environ.get("PSQL_DSN_DEVO")
        sql = "SELECT seq,guest_user_id,inviter_user_id,created_at FROM inviter WHERE guest_user_id = %s AND delete_flag IS FALSE ORDER BY created_at DESC"

        with psycopg2.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(sql,(joinUser,))
                res = cur.fetchall()

        if len(res) == 0:
            inviteUser = "unknown"
        elif res[0][2] == None:
            inviteUser = "unknown"
        else:
            inviteUser = res[0][2]

        welcome_channel_id = os.environ.get("SLACK_WELCOME_CHANNEL_ID")
        message = create_intro_message(joinUser,inviteUser)
        say(text=message, channel=welcome_channel_id)

        # delete flag
        upd_sql = "UPDATE inviter SET delete_flag = TRUE WHERE guest_user_id = %s"
        with psycopg2.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(upd_sql,(joinUser,))

# TODO:add mention command
@app.message(re.compile('^devo '))
def handle_message_events(say, logger, context, message):
    logger.debug(context)
    
    input_text = message['text']
    command = input_text.removeprefix("devo ")
    
    if command == "help":
        say(file_read("help.txt"))

    if command == "ping":
        say('PONG')

    if command == "sugaicat":
        #mg = mugi.mugiRandClass()
        #filepath = mg.get_file()
        channel = message['channel']
        #filename = mg.filename
        #title = "撮影日：" + mg.createDate.strftime('%Y-%m-%d')
        filepath = select_sugaicat_file()
        filename = os.path.basename(filepath)
        title = filename
        app.client.files_upload_v2(
                channel=channel,
                file=filepath,
                filename=filename,
                title=title
        )

    if command == "intro_test":
        test_user_id = os.environ.get("TEST_USER_ID")
        say(create_intro_message(test_user_id,test_user_id))

    if command == "jikkainu":
        data = select_random_jikkainu()
        tid = data[0][0]
        url = "https://fxtwitter.com/jikkainu/status/" + tid
        text = data[0][1]
        message = text
        message += "\n"
        message += url
        say(message)

    if command[:4] == "img ":
        keyword = command.removeprefix("img ")
        img_list = get_search_img(keyword)
        img_data = random.choice(img_list)
        message = img_data.get("link")
        message += "\n<"
        message += img_data.get("thmb")
        message += "|(thumbnail)>"
        say(message)

    if command[:6] == "image ":
        keyword = command.removeprefix("image ")
        img_list = get_search_img(keyword)
        img_data = random.choice(img_list)
        message = img_data.get("link")
        message += "\n<"
        message += img_data.get("thmb")
        message += "|(thumbnail)>"
        say(message)

# shinraisha
@app.action("shinraisha")
def handle_action_shinraisha(ack, body, logger):
    ack()
    logger.debug(body)

    dsn = os.environ.get("PSQL_DSN_DEVO")

    ch_id = body.get("channel").get("id")
    user_id = body.get("user").get("id")

    # check duplicate
    sel_sql = "select count(*) from shinrai where user_id = %s and click_at between %s and %s"
    sel_sql_dc = "select count(*) from shinrai where click_at between %s and %s"
    sel_sql_tc = "select count(*) from shinrai where user_id = %s"
    today_str = datetime.datetime.today().strftime("%Y-%m-%d")
    begin_str = today_str + " 6:30"
    end_str = today_str + " 7:31"
    with psycopg2.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(sel_sql,(user_id,begin_str,end_str))
                count_res = cur.fetchall()
            with conn.cursor() as cur:
                cur.execute(sel_sql_dc,(begin_str,end_str))
                count_dc = cur.fetchall()
            with conn.cursor() as cur:
                cur.execute(sel_sql_tc,(user_id,))
                count_tc = cur.fetchall()
   
    if count_res[0][0] == 0:
        ins_sql = "INSERT INTO shinrai (user_id) VALUES(%s)"
        with psycopg2.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(ins_sql,(user_id,))
        
        filetext = file_read("shinraisha.txt")
        message = filetext.format(str(count_dc[0][0]+1),str(count_tc[0][0]+1))

        app.client.chat_postEphemeral(
            channel=ch_id,
            user=user_id,
            text=message
        )
    else:
        app.client.chat_postEphemeral(
            channel=ch_id,
            user=user_id,
            text="あなたは既に今日の :shinraisha: です！"
        )
#shinrai-rank
@app.action("shinrai-rank")
def handle_action_shinrai_rank(ack, body, logger):
    ack()
    logger.debug(body)

    dsn = os.environ.get("PSQL_DSN_DEVO")

    ch_id = body.get("channel").get("id")
    user_id = body.get("user").get("id")

    sql = "select rnk.user_id, rnk.cnt, rnk.ranking from (select user_id,count(user_id) AS cnt,rank() OVER (ORDER BY count(user_id) desc) AS ranking from shinrai group by user_id order by count(user_id) desc) AS rnk where rnk.user_id = %s"
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql,(user_id,))
            results = cur.fetchall()

    if len(results) != 0:
        message = "あなたはランキング"
        message += str(results[0][2])
        message += "位で、通算"
        message += str(results[0][1])
        message += "回です"
    else:
        message = "あなたはまだランキングに記載されていません"

    app.client.chat_postEphemeral(
            channel=ch_id,
            user=user_id,
            text=message
    )


#shinrai-help
@app.action("shinrai-help")
def handle_action_shinrai_help(ack, body, logger):
    ack()
    logger.debug(body)

    ch_id = body.get("channel").get("id")
    user_id = body.get("user").get("id")

    app.client.chat_postEphemeral(
            channel=ch_id,
            user=user_id,
            text=":kawagoe: 氏の「休日に早起きするやつは信頼できる」という格言をもとに作成されました。\n土日祝日の AM6:30 - AM7:30 の間に起床した人を記録します。\n（blackholeの機能により起床ボタンが消えて押せなくなることを利用しています）\n自己申告制なので、夜更かしでも二度寝でも大丈夫！\n何かあれば、devo管理人のyamagataまでどうぞ"
    )


# other message
@app.event("message")
def handle_message_events(body, logger):
    logger.debug(body)

# app start
if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
