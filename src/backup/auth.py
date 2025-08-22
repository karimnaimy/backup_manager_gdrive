"""Google Drive authentication for headless environments."""

import os.path
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .config import GoogleDriveConfig

SCOPES = ['https://www.googleapis.com/auth/drive.file']


class GoogleDriveAuth:
    """Handle Google Drive authentication for headless environments."""
    
    def __init__(self, config: GoogleDriveConfig):
        self.config = config
        self._service = None
    
    def authenticate_headless(self) -> None:
        """Authenticate using manual flow for headless servers."""
        creds = self._load_existing_credentials()
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("Refreshing expired token...")
                creds.refresh(Request())
            else:
                print("No valid credentials found. Starting authentication flow...")
                creds = self._get_new_credentials()
            
            self._save_credentials(creds)
        
        self._service = build('drive', 'v3', credentials=creds)
        print("Successfully authenticated with Google Drive")
    
    def _load_existing_credentials(self) -> Optional[Credentials]:
        """Load existing credentials from token file."""
        if self.config.token_file.exists():
            return Credentials.from_authorized_user_file(str(self.config.token_file), SCOPES)
        return None
    
    def _get_new_credentials(self) -> Credentials:
        """Get new credentials using manual authorization flow."""
        if not self.config.credentials_file.exists():
            raise FileNotFoundError(
                f"Credentials file not found: {self.config.credentials_file}\n"
                "Please download OAuth2 credentials from Google Cloud Console"
            )
        
        flow = InstalledAppFlow.from_client_secrets_file(
            str(self.config.credentials_file), 
            SCOPES
        )
        flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
        
        auth_url, _ = flow.authorization_url(prompt='consent')
        print(f"\nPlease visit this URL to authorize the application:")
        print(f"{auth_url}")
        print(f"\nAfter authorization, you'll receive a code.")
        print("Copy the authorization code and paste it below:")
        
        code = input("Authorization code: ").strip()
        flow.fetch_token(code=code)
        
        return flow.credentials
    
    def _save_credentials(self, creds: Credentials) -> None:
        """Save credentials to token file."""
        self.config.token_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config.token_file, 'w') as token:
            token.write(creds.to_json())
        print(f"Credentials saved to {self.config.token_file}")
    
    @property
    def service(self):
        """Get the Google Drive service instance."""
        if self._service is None:
            raise RuntimeError("Not authenticated. Call authenticate_headless() first.")
        return self._service
    
    def test_connection(self) -> bool:
        """Test the connection to Google Drive."""
        try:
            self.service.about().get(fields="user").execute()
            return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False