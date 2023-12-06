import json
from pathlib import Path
import logging

from utils import gmail_authenticate, send_message, sorteo


def main(dry_run: bool = False, owner_name: str = "Santiago"):
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
    if not dry_run:
        # get the Gmail API service
        service = gmail_authenticate()

        for gifter, gifted in results.items():
            body = f"""Te toca regalarle a {gifted}, buena suerte"""
            if gifted == owner_name:
                body = f"""Te toca regalarle a {gifted}, más vale que pienses un buen regalo"""
            message = send_message(service= service,
                sender=our_email,
                destination= participants[gifter],
                obj= 'Amigo invisible',
                body= body
            )

if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())
    dry_run_input = input("Dry run? [Y/n]")
    dry_run = not dry_run_input == "n"
    logger.info('Dry run is: %s', dry_run)
    main(dry_run)
