import json
from pathlib import Path

from utils import gmail_authenticate, send_message, sorteo


def main():
    our_email = "santiagocebellanbot@gmail.com"

    with open('config/participants.json', 'r') as file:
        participants = json.load(file)
    
    if Path('config/disallowed_pairs.txt').is_file():
        with open('config/disallowed_pairs.txt', 'r') as file:
            disallowed_pairs_raw = file.readlines()
        disallowed_pairs: list[tuple[str, str]] = [tuple(line.split(',', 1))
                                                   for line in disallowed_pairs_raw]
    else:
        disallowed_pairs: list[tuple[str, str]] = []
        
    results = sorteo(list(participants.keys()), disallowed_pairs)

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
