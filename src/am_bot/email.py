"""This module provides functionality for sending emails using different email services.

It focuses on Gmail and OAuth2 authentication. It includes classes and functions
to construct email messages, handle authentication, and send emails via the Gmail API.

Usage:
    This module is intended to be used as part of a larger application that requires
    sending emails via different email services, particularly Gmail. The `GmailService`
    class provides a concrete implementation for sending emails using the Gmail API
    with OAuth2 authentication.
"""

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

if ty.TYPE_CHECKING:  # pragma: no cover, this is only used for type checking
    from google.oauth2.credentials import Credentials as GoogleCredentials


# Define the supported email services
@verify(UNIQUE)
class SupportedEmailServices(Enum):
    """Enum class representing supported email services.

    Attributes:
        GMAIL (str): Represents the Gmail email service.
    """

    GMAIL = 'gmail'


@dataclass
class AuthParams:
    """Common parameters for the authentication backends.

    Attributes:
        service (SupportedEmailServices): The email service being used.
        creds_path (Path): The path to the credentials file. Defaults to the current working directory joined with 'credentials'.
        interactive (bool): Indicates if the authentication should be interactive. Defaults to True.
    """

    service: SupportedEmailServices
    creds_path: Path = Path.cwd() / 'credentials'
    interactive: bool = True  # Interactive true by default because it's the only supported method


class EmailService(ABC):
    """Interface for the email services."""

    @abstractmethod
    def __init__(self, auth_params: 'AuthService') -> None: ...

    @abstractmethod
    def send_email(self, email: 'MIMEText | MIMEMultipart') -> None: ...


def build_message(
    sender: str, destination: str, obj: str, body: str, attachments: ty.Optional[list[str]] = None
) -> MIMEText | MIMEMultipart:
    """Constructs an email message with optional attachments.

    Args:
        sender (str): The email address of the sender.
        destination (str): The email address of the recipient.
        obj (str): The subject of the email.
        body (str): The body content of the email.
        attachments (Optional[list[str]]): A list of file paths to attach to the email. Defaults to None.

    Returns:
        MIMEText | MIMEMultipart: The constructed email message, either as a MIMEText object (if no attachments)
        or a MIMEMultipart object (if attachments are provided).
    """
    if attachments is None:
        attachments = []
    if not attachments:  # no attachments given
        message = MIMEText(body)
        message['to'] = destination
        message['from'] = sender
        message['subject'] = obj
    else:  # pragma: no cover
        # This is not supported yet
        message = MIMEMultipart()
        message['to'] = destination
        message['from'] = sender
        message['subject'] = obj
        message.attach(MIMEText(body))
        for filename in attachments:
            message.add_attachment(message, filename)
    return message


class GmailService(EmailService):
    """GmailService class provides functionality to send emails using the Gmail API with OAuth2 authentication.

        TYPE (SupportedEmailServices): The type of email service, set to SupportedEmailServices.GMAIL.
        SCOPES (list): The OAuth2 scopes required for accessing the Gmail API.

    Methods:
        __init__(auth_helper: 'GoogleAuthService') -> None:
            Initializes the email service with OAuth2 authentication.


        send_email(email: 'MIMEText | MIMEMultipart') -> None:
            Sends an email using the Gmail API.
    """

    TYPE = SupportedEmailServices.GMAIL
    SCOPES = ['https://mail.google.com/']

    def __init__(self, auth_helper: 'GoogleAuthService') -> None:
        """Initializes the email service with OAuth2 authentication.

        Args:
            auth_helper (GoogleAuthService): An instance of GoogleAuthService to handle OAuth2 authentication.

        Attributes:
            _oauth_token: The OAuth2 token obtained from the auth_helper.
            _service: The Gmail API service built using the OAuth2 token.
        """
        self._oauth_token = auth_helper.get_oauth2_token(self.SCOPES)
        self._service: ty.Any = build('gmail', 'v1', credentials=self._oauth_token)

    def send_email(self, email: 'MIMEText | MIMEMultipart') -> None:
        """Sends an email using the Gmail API.

        Args:
            email (MIMEText | MIMEMultipart): The email message to be sent. It should be an instance of either
                                              MIMEText or MIMEMultipart from the email.mime module.

        Returns:
            None
        """
        body = {'raw': urlsafe_b64encode(email.as_bytes()).decode()}
        (self._service.users().messages().send(userId='me', body=body).execute())


class AuthService(ABC):
    """Interface for the authentication backends."""

    @abstractmethod
    def __init__(self, params: AuthParams) -> None: ...


class GoogleAuthService(AuthService):
    """GoogleAuthService is a class that handles authentication for Google services using OAuth2.

    Attributes:
        TYPE (SupportedEmailServices): Specifies the type of email service, set to GMAIL.

    Methods:
        __init__(params: AuthParams) -> None:
            Initializes the email authentication parameters and loads credentials from a JSON file.
        get_oauth2_token(scopes: list[str]) -> 'GoogleCredentials':
            Obtain an OAuth2 token for accessing Google APIs.
        manual_auth_flow(scopes: list[str]) -> 'GoogleCredentials':
            Initiates a manual authentication flow for obtaining Google credentials.
    """

    TYPE = SupportedEmailServices.GMAIL

    def __init__(self, params: AuthParams) -> None:
        """Initializes the email authentication parameters and loads credentials from a JSON file.

        Args:
            params (AuthParams): The authentication parameters containing the credentials path.

        Raises:
            FileNotFoundError: If the credentials file is not found at the specified path.
                the file token.pickle stores the user's access and refresh tokens, and is
                created automatically when the authorization flow completes for the first time.
        """
        self.params: AuthParams = params
        self.json_path = params.creds_path / self.TYPE.value / 'credentials.json'
        try:
            self._creds: dict[str, str | dict[str, str]] = json.loads(self.json_path.read_text())
        except FileNotFoundError:
            raise FileNotFoundError(f'No credentials file found at {self.json_path}') from None

    def get_oauth2_token(self, scopes: list[str]) -> 'GoogleCredentials':
        """Obtain an OAuth2 token for accessing Google APIs.

        This method initiates the OAuth2 authentication flow to obtain a token
        with the specified scopes. Currently, only interactive authentication
        is supported.

        Args:
            scopes (list[str]): A list of scopes specifying the access permissions.

        Returns:
            GoogleCredentials: The obtained OAuth2 token credentials.

        Raises:
            NotImplementedError: If non-interactive authentication is attempted.
        """
        if self.params.interactive:
            return self.manual_auth_flow(scopes)
        else:
            raise NotImplementedError('Non-interactive authentication is not supported yet.')

    def manual_auth_flow(self, scopes: list[str]) -> 'GoogleCredentials':
        """Initiates a manual authentication flow for obtaining Google credentials.

        This method uses the `InstalledAppFlow` from the `google-auth` library to
        create a local server for user authentication and authorization.

        Args:
            scopes (list[str]): A list of OAuth 2.0 scopes that specify the level of access
                                requested by the application.

        Returns:
            GoogleCredentials: The authenticated Google credentials object.
        """
        flow = InstalledAppFlow.from_client_secrets_file(self._creds, scopes=scopes)
        return flow.run_local_server(port=0)
