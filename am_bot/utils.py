import os
import pickle
# Gmail API utils
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
# for encoding/decoding messages in base64
from base64 import urlsafe_b64decode, urlsafe_b64encode
# for dealing with attachement MIME types
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
import random
from collections import deque


# Request all access (permission to read/send/receive emails, manage the inbox, and more)
SCOPES = ['https://mail.google.com/']

def gmail_authenticate(creds_path: Path = Path.cwd() / 'credentials'):
    creds = None
    # the file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time
    token_path = creds_path / "token.pickle"
    json_path = creds_path / "credentials.json"
    if token_path.exists():
        with open(token_path, "rb") as token:
            creds = pickle.load(token)
    # if there are no (valid) credentials availablle, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(json_path), SCOPES)
            creds = flow.run_local_server(port=0)
        # save the credentials for the next run
        with open(token_path, "wb") as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)


def build_message(sender, destination, obj, body, attachments=[]):
    if not attachments: # no attachments given
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
            add_attachment(message, filename)
    return {'raw': urlsafe_b64encode(message.as_bytes()).decode()}

def send_message(service, sender, destination, obj, body, attachments=[]):
    return service.users().messages().send(
      userId="me",
      body=build_message(sender, destination, obj, body, attachments)
    ).execute()
    
    
def sorteo(participants: list):
    if not participants:
        raise ValueError("No participants!")
    idxs = [i for i in range(len(participants))]
    random.shuffle(idxs)
    
    givers = idxs
    receivers = deque(givers)
    receivers.rotate(1)
    return {participants[g]: participants[r] for g, r in zip(givers, receivers)}
        
    
    