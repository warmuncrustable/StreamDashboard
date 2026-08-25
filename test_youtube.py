import os

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly"
]

CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "youtube_token.json"


def main():

    credentials = None

    if os.path.exists(TOKEN_FILE):

        credentials = Credentials.from_authorized_user_file(
            TOKEN_FILE,
            SCOPES,
        )

    if credentials and credentials.expired:

        if credentials.refresh_token:
            credentials.refresh(Request())
        else:
            credentials = None

    if not credentials:

        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_FILE,
            SCOPES,
        )

        credentials = flow.run_local_server(
            port=0,
            access_type="offline",
            prompt="consent",
        )

    with open(TOKEN_FILE, "w") as token:

        token.write(
            credentials.to_json()
        )

    os.chmod(
        TOKEN_FILE,
        0o600
    )

    print("YouTube authentication successful.")
    print(f"Token saved to {TOKEN_FILE}")


if __name__ == "__main__":
    main()
