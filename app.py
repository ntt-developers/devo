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
# TODO: setting by config value
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

# ---event function---

@app.event("member_joined_channel")
def ask_for_introduction(body, logger, say):
    logger.debug(body)

    general_channel_id = os.environ.get("SLACK_GENERAL_CHANNEL_ID")

    # join to general channel -> new person join
    if body['event']['channel'] == general_channel_id:
        joinUserName = body['event']['user']

        # in some cases, 'inviter' is null
        if 'inviter' in body['event']:
            inviteUserName = body['event']['inviter']
        else:
            inviteUserName = "unknown"
        
        welcome_channel_id = os.environ.get("SLACK_WELCOME_CHANNEL_ID")
        message = create_intro_message(joinUserName,inviteUserName)
        say(text=message, channel=welcome_channel_id)

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
        path = "sugaicat.txt"
        with open(path) as f:
            lines = f.readlines()

        rand_max = 797
        say(lines[random.randint(0,rand_max-1)])
    
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
