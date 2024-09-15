import json
import logging
from pathlib import Path

from am_bot.email import AuthParams, GmailService, GoogleAuthService, build_message
from am_bot.lottery import generate_lottery


def main(dry_run: bool = False, title: str = 'Amigo Invisible', owner_name: str = 'Santiago'):
    our_email = 'santiagocebellanbot@gmail.com'

    with open('config/participants.json') as file:
        participants = json.load(file)

    if Path('config/disallowed_pairs.txt').is_file():
        with open('config/disallowed_pairs.txt') as file:
            disallowed_pairs_raw = file.readlines()
        disallowed_pairs: list[tuple[str, str]] = [tuple(line.strip().split(',', 1)) for line in disallowed_pairs_raw]
    else:
        disallowed_pairs: list[tuple[str, str]] = []

    results = generate_lottery(list(participants.keys()), disallowed_pairs)
    if not dry_run:
        auth_params = AuthParams(GmailService.TYPE, creds_path=Path.cwd() / 'credentials', interactive=True)
        google_auth = GoogleAuthService(auth_params)
        # This will require user interaction
        gmail_service = GmailService(google_auth)

        for gifter, gifted in results.items():
            body = f"""Te toca regalarle a {gifted}, buena suerte.
            
            Nota: Ignora el mensaje previo. Fue una prueba"""
            if gifted == owner_name:
                body = f"""Te toca regalarle a {gifted}, más vale que pienses un buen regalo"""
            message = build_message(sender=our_email, destination=participants[gifter], obj=title, body=body)
            gmail_service.send_email(message)
    else:
        for gifter, gifted in results.items():
            print(f'{gifter} regala a {gifted}')


if __name__ == '__main__':
    title = 'Amigo Invisible Martinez+'
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())
    # dry_run_input = input("Dry run? [Y/n]")
    # dry_run = not dry_run_input == "n"
    # logger.info('Dry run is: %s', dry_run)
    main(True, title=title)
