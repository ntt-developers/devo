import pickle
import os.path
import psycopg2
import datetime
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/photoslibrary']
API_SERVICE_NAME = 'photoslibrary'
API_VERSION = 'v1'
CLIENT_SECRET_FILE = os.environ["CLIENT_SECRET_FILE"]
TOKEN_FILE = os.environ["TOKEN_FILE"]

dsn = os.environ["DSN"]

def get_authenticated_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)

    return build(API_SERVICE_NAME, API_VERSION, credentials=creds,static_discovery=False)

# True -> exists, False -> Not exists
def checkId(pid):
    sql = "select count(*) from mugi where id = %s"
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql,(pid,))
            results = cur.fetchall()
    count = int(results[0][0])
    if count == 0:
        return False
    else:
        return True

def getPhotos(service, albumId):
    nextPageTokenMediaItems = ''
    while True:
        body = {
            'albumId' : albumId,
            'pageSize' : 100,
            'pageToken' : nextPageTokenMediaItems
        }
        mediaItems = service.mediaItems().search(body=body).execute()

        sql = "insert into mugi values(%s,%s,%s,%s,%s,%s,%s)"
        break_flag = False
        with psycopg2.connect(dsn) as conn:
            with conn.cursor() as cur:
                for mediaItem in mediaItems['mediaItems']:
                    pid = mediaItem['id']
                    if checkId(pid):
                        break_flag = True
                        continue

                    purl = mediaItem['productUrl']
                    mime = mediaItem['mimeType']
                    filename = mediaItem['filename']
                    mediaData = mediaItem['mediaMetadata']
                    ctime = datetime.datetime.fromisoformat(mediaData['creationTime'].replace('Z','+00:00'))
                    width = mediaData['width']
                    height = mediaData['height']

                    cur.execute(sql,(pid,purl,mime,ctime,width,height,filename))
        if ('nextPageToken' in mediaItems) and not break_flag:
            nextPageTokenMediaItems = mediaItems['nextPageToken']
        else:
            break

def main():
    service = get_authenticated_service()
    albumId = os.environ["ALB_ID"]
    getPhotos(service, albumId)

# app start
if __name__ == "__main__":
    main()
