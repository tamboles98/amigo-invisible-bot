import typing as ty
from pathlib import Path
from unittest.mock import Mock, create_autospec

import faker
import pytest
from google.oauth2.credentials import Credentials as GoogleCredentials

from am_bot import email

if ty.TYPE_CHECKING:
    pass

FIXTURES_DIR = Path.cwd() / 'tests' / 'data'


@pytest.fixture
def auth_params() -> email.AuthParams:
    return email.AuthParams(email.SupportedEmailServices.GMAIL, creds_path=FIXTURES_DIR / 'credentials')


@pytest.fixture
def mock_google_auth(monkeypatch: ty.Any) -> Mock:
    oauth_provider_class = create_autospec(email.InstalledAppFlow, instance=False)
    oauth_provider = create_autospec(email.InstalledAppFlow, instance=True)
    oauth_provider_class.from_client_secrets_file.return_value = oauth_provider
    oauth_provider.run_local_server.return_value = fake_token_factory()

    monkeypatch.setattr(email, 'InstalledAppFlow', oauth_provider_class)
    return oauth_provider


@pytest.fixture
def mock_gmail_service(monkeypatch: ty.Any) -> Mock:
    gmail_service_builder = create_autospec(email.build)
    google_service = Mock()
    gmail_service_builder.return_value = google_service

    monkeypatch.setattr(email, 'build', gmail_service_builder)
    return google_service


def fake_token_factory() -> GoogleCredentials:
    # creds: dict[str, dict[str, str]], scopes: list[str]
    # installed = creds['installed']
    fake = faker.Faker()
    return GoogleCredentials(
        token=fake.sha256(),
        refresh_token=fake.sha256(),
        id_token=None,
        token_uri=fake.uri(),  # installed['token_uri'],
        client_id=fake.sha256(),  # installed['client_id'],
        client_secret=fake.sha256(),  # installed['client_secret'],
        scopes=email.GmailService.SCOPES,  # scopes,
    )


def test_build_email_message():
    body = 'Test email'
    destination = 'fake_guy@fakecompany.com'
    sender = 'myself@mycompany.com'
    obj = 'Test email'
    email.build_message(sender, destination, obj, body)


class TestGoogleAuthService:
    def test_init(self, auth_params: email.AuthParams):
        google_auth = email.GoogleAuthService(auth_params)
        assert google_auth.params == auth_params
        assert google_auth.json_path == auth_params.creds_path / 'gmail' / 'credentials.json'
        assert isinstance(google_auth._creds, dict)

    def test_manual_auth_flow(self, auth_params: email.AuthParams, mock_google_auth: Mock):
        google_auth = email.GoogleAuthService(auth_params)
        assert google_auth.manual_auth_flow(scopes=email.GmailService.SCOPES) is not None

    def test_get_oauth2_token_manual(self, auth_params: email.AuthParams, monkeypatch: ty.Any):
        auth_params.interactive = True
        manual_flow_mock = create_autospec(email.GoogleAuthService.manual_auth_flow, return_value=fake_token_factory())
        monkeypatch.setattr(email.GoogleAuthService, 'manual_auth_flow', manual_flow_mock)
        google_auth = email.GoogleAuthService(auth_params)
        assert google_auth.get_oauth2_token(scopes=email.GmailService.SCOPES) is not None

    def test_get_oauth2_token_auto(self, auth_params: email.AuthParams):
        # Modify the auth_params to be non-interactive
        auth_params.interactive = False
        google_auth = email.GoogleAuthService(auth_params)
        with pytest.raises(NotImplementedError):
            google_auth.get_oauth2_token(scopes=email.GmailService.SCOPES)


class TestGmailService:
    def test_init(self, auth_params: email.AuthParams, mock_google_auth: Mock):
        google_auth = email.GoogleAuthService(auth_params)
        gmail_service = email.GmailService(google_auth)
        assert gmail_service._oauth_token is not None
        assert gmail_service._service is not None

    def test_send_email(self, auth_params: email.AuthParams, mock_google_auth: Mock, mock_gmail_service: Mock):
        # Very dummy test, to test properly we would need to send an actual email
        google_auth = email.GoogleAuthService(auth_params)
        gmail_service = email.GmailService(google_auth)
        email_message = email.MIMEText('Test email')
        gmail_service.send_email(email_message)
