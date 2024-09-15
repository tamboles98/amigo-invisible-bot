import json
import typing as ty
from abc import ABC, abstractmethod
from base64 import urlsafe_b64encode
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import UNIQUE, Enum, verify
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

# Gmail API utils
from googleapiclient.discovery import build

if ty.TYPE_CHECKING:
    from google.oauth2.credentials import Credentials as GoogleCredentials


# Define the supported email services
@verify(UNIQUE)
class SupportedEmailServices(Enum):
    GMAIL = 'gmail'


@dataclass
class AuthParams:
    """Common parameters for the authentication backends."""

    service: SupportedEmailServices
    creds_path: Path = Path.cwd() / 'credentials'
    interactive: bool = True  # Interactive true by default because it's the only supported method


class EmailService(ABC):
    """Interface for the email services."""

    @abstractmethod
    def __init__(self, auth_params: 'AuthService') -> None:
        self.auth_params = auth_params

    @abstractmethod
    def send_email(self, email: 'MIMEText | MIMEMultipart') -> None:
        pass


class GmailService(EmailService):
    TYPE = SupportedEmailServices.GMAIL
    SCOPES = ['https://mail.google.com/']

    def __init__(self, auth_helper: 'GoogleAuthService') -> None:
        self._oauth_token = auth_helper.get_oauth2_token(self.SCOPES)
        self._service: ty.Any = build('gmail', 'v1', credentials=self._oauth_token)

    def send_email(self, email: 'MIMEText | MIMEMultipart') -> None:
        body = {'raw': urlsafe_b64encode(email.as_bytes()).decode()}
        (self._service.users().messages().send(userId='me', body=body).execute())


class AuthService(ABC):
    """Interface for the authentication backends."""

    @abstractmethod
    def __init__(self, params: AuthParams) -> None:
        pass


def build_message(
    sender: str, destination: str, obj: str, body: str, attachments: ty.Optional[list[str]] = None
) -> MIMEText | MIMEMultipart:
    if attachments is None:
        attachments = []
    if not attachments:  # no attachments given
        message = MIMEText(body)
        message['to'] = destination
        message['from'] = sender
        message['subject'] = obj
    else:
        message = MIMEMultipart()
        message['to'] = destination
        message['from'] = sender
        message['subject'] = obj
        message.attach(MIMEText(body))
        for filename in attachments:
            message.add_attachment(message, filename)
    return message


class GoogleAuthService(AuthService):
    TYPE = SupportedEmailServices.GMAIL

    def __init__(self, params: AuthParams) -> None:
        # the file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time
        self.params: AuthParams = params
        self.json_path = params.creds_path / self.TYPE.value / 'credentials.json'
        try:
            self._creds: dict[str, str | dict[str, str]] = json.loads(self.json_path.read_text())
        except FileNotFoundError:
            raise FileNotFoundError(f'No credentials file found at {self.json_path}') from None

    def get_oauth2_token(self, scopes: list[str]) -> 'GoogleCredentials':
        if self.params.interactive:
            return self.manual_auth_flow(scopes)
        else:
            raise NotImplementedError('Non-interactive authentication is not supported yet.')

    def manual_auth_flow(self, scopes: list[str]) -> 'GoogleCredentials':
        flow = InstalledAppFlow.from_client_secrets_file(self._creds, scopes=scopes)
        return flow.run_local_server(port=0)
