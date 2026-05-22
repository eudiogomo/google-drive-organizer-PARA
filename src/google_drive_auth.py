import json
import os
from typing import Any

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/drive"]


class GoogleDriveAuth:
    def __init__(self, credentials_file: str = "credentials.json", token_file: str = "token.json"):
        self.credentials_file = credentials_file
        self.token_file = token_file

    def authenticate(self) -> Any:
        """
        Handles full OAuth2 flow:
        1. Try to load cached token from token.json
        2. If expired but has refresh_token, refresh automatically
        3. If no valid credentials, run InstalledAppFlow (opens browser)
        4. Save refreshed/new credentials back to token.json
        5. Return built Drive API service object
        """
        creds = None
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except RefreshError:
                    os.remove(self.token_file)
                    creds = None

            if not creds:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"credentials.json not found at '{self.credentials_file}'. "
                        "Download it from the Google Cloud Console and place it in the project root."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)

            with open(self.token_file, "w") as token:
                token.write(creds.to_json())

        return build("drive", "v3", credentials=creds)
