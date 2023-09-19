#
# gphotoClass.py
#
import pickle
import os
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

class gphotoClass():
    SCOPES = ['https://www.googleapis.com/auth/photoslibrary']
    API_SERVICE_NAME = 'photoslibrary'
    API_VERSION = 'v1'
    CLIENT_SECRET_FILE = os.environ["CLIENT_SECRET_FILE"]
    TOKEN_FILE = os.environ["TOKEN_FILE"]
    service = None
    
    def __init__(self):
        self.service = self.get_authenticated_service()

    def get_authenticated_service(self):
        creds = None
        if os.path.exists(self.TOKEN_FILE):
            with open(self.TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.CLIENT_SECRET_FILE, self.SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(self.TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)

        return build(self.API_SERVICE_NAME, self.API_VERSION, credentials=creds,static_discovery=False)

    def get_base_url(self, pid):
        mediaItem = self.service.mediaItems().get(mediaItemId=pid).execute()
        burl = mediaItem['baseUrl']
        return burl
