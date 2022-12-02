import json

from utils import gmail_authenticate, send_message, sorteo


def main():
    our_email = "santiagocebellanbot@gmail.com"

    with open('config/participants.json', 'rb') as file:
        participants = json.load(file)
        
    results = sorteo(list(participants.keys()))

    # get the Gmail API service
    service = gmail_authenticate()

    for gifter, gifted in results.items():
        message = send_message(service= service,
            sender=our_email,
            destination= participants[gifter],
            obj= 'Amigo invisible',
            body= f"""Te toca regalarle a {gifted}, buena suerte"""
        )

if __name__ == '__main__':
    main()
