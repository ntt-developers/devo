import os
import logging
import re
import random
import psycopg2
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

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

def select_random_url():
    dsn = os.environ.get("PSQL_DSN_DOG")
    sql = "SELECT * FROM twurl WHERE index=(SELECT (max(index) * random())::int FROM twurl)"
    
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            results = cur.fetchall()
    return results[0][1]

def select_random_file():
    path = os.environ["SUGAICAT_PATH"]
    files = os.listdir(path)
    files_file = [f for f in files if os.path.isfile(os.path.join(path, f))]
    fileone = random.choice(files_file)
    return os.path.join(path, fileone)

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
        else:
            inviteUser = res[0][2]

        welcome_channel_id = os.environ.get("SLACK_WELCOME_CHANNEL_ID")
        message = create_intro_message(joinUser,inviteUser)
        say(text=message, channel=welcome_channel_id)

        # delete flag
        if len(res) != 0:
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
        filepath = select_random_file()
        channel = message['channel']
        filename = os.path.basename(filepath)
        title = "sugaicat"
        app.client.files_upload(
                channels=channel,
                file=filepath,
                filename=filename,
                title=title
        )

    if command == "intro_test":
        test_user_id = os.environ.get("TEST_USER_ID")
        say(create_intro_message(test_user_id,test_user_id))

    if command == "jikkainu":
        say(select_random_url())

# other message
@app.event("message")
def handle_message_events(body, logger):
    logger.debug(body)


# app start
if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
