import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/drive"]


class GoogleDriveAuth:
    def __init__(self, credentials_file: str = "credentials.json", token_file: str = "token.pickle"):
        self.credentials_file = credentials_file
        self.token_file = token_file

    def authenticate(self):
        """
        Handles full OAuth2 flow:
        1. Try to load cached token from token.pickle
        2. If expired but has refresh_token, refresh automatically
        3. If no valid credentials, run InstalledAppFlow (opens browser)
        4. Save refreshed/new credentials back to token.pickle
        5. Return built Drive API service object
        """
        creds = None
        if os.path.exists(self.token_file):
            with open(self.token_file, "rb") as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(self.token_file, "wb") as token:
                pickle.dump(creds, token)

        return build("drive", "v3", credentials=creds)
