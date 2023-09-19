#
# mugiRandClass.py
#
import os
import psycopg2
import requests
import datetime
import urllib.error
import urllib.request
from mugiRand import gphotoClass as gp
from zoneinfo import ZoneInfo

class mugiRandClass():
    dsn = None
    tmp_f = None
    pid = None
    burl = None
    filename = None
    mime = None
    temp_file = None
    createDate = None

    def select_random_pid(self):
        sql = "SELECT id,mime_type,creation_time,filename FROM mugi order by random() limit 1"
        with psycopg2.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                results = cur.fetchall()

        self.pid = results[0][0]
        self.mime = results[0][1]
        self.createDate = results[0][2].astimezone(ZoneInfo("Asia/Tokyo"))
        self.filename = results[0][3]

    def get_burl(self):
        gpi = gp.gphotoClass()
        self.burl = gpi.get_base_url(self.pid)

    def get_file(self):
        if self.mime.startswith("video"):
            self.temp_file = os.path.join(self.tmp_f, "tmp.mp4")
        elif self.mime.startswith("image"):
            self.temp_file = os.path.join(self.tmp_f, "tmp.jpg")
        else:
            self.temp_file = os.path.join(self.tmp_f, self.filename)

        if self.mime.startswith("video"):
            self.burl = self.burl + "=dv"
        else:
            self.burl = self.burl + "=d"

        self.download_file()
        return self.temp_file

    def download_file(self):
        try:
            with urllib.request.urlopen(self.burl) as web_file, open(self.temp_file, 'wb') as local_file:
                local_file.write(web_file.read())
        except urllib.error.URLError as e:
            print(e)

    def delete_tmp_file(self):
        os.remove(self.temp_file)

    def __init__(self):
        self.dsn = os.environ["DSN"]
        self.tmp_f = os.environ["TMP_F"]
        self.select_random_pid()
        self.get_burl()
