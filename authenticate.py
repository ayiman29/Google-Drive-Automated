import os
import pickle
import google.auth
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.auth.exceptions import RefreshError


SCOPES = ['https://www.googleapis.com/auth/drive']

TOKEN_FILE = 'token.pickle'
CREDENTIALS_FILE = 'credentials.json' 

def authenticate():
    creds = None


    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)

  
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except RefreshError:
            os.remove(TOKEN_FILE)
            creds = None


    if not creds or not creds.valid:
        try:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        except ValueError as e:
            import json
            with open(CREDENTIALS_FILE, 'r') as f:
                client_config = json.load(f)
            if "installed" not in client_config and "web" not in client_config:
                flow = InstalledAppFlow.from_client_config({"installed": client_config}, SCOPES)
            else:
                raise e
        creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)