from datetime import datetime
import time
import json

from tennis_club import TennisClub
from tipper_scraper import TipperScraper
from email_manager import EmailManager
from program_args import get_args

def main():
    with open(get_args().course_config_path) as f:
        tipper_config = json.load(f)

    TipperScraper.set_scraping_details(tipper_config['xml_objects'])

    tennis_courts = {}

    for course_config in tipper_config['court_locations']:
        tennis_court = TennisClub(course_config)
        tennis_courts[tennis_court.name] = tennis_court

    print('Getting new tennis times')
    print(datetime.now())
    new_tennis_times_by_location = {}
    t0 = time.time()

    for tennis_court in tennis_courts.values():
        print(f'{tennis_court.name}')
        new_tennis_times = tennis_court.get_new_tee_times_for_period(tipper_config['min_spots'])
        if new_tennis_times:
            print(f'New times at {tennis_court.name}')
            new_tennis_times_by_location[tennis_court.name] = new_tennis_times
    if new_tennis_times_by_location:
        email_manager = EmailManager(get_args().local, tipper_config['email_details'])
        email_manager.create_and_send_email("new_tennis_times", tennis_sessions_by_location=new_tennis_times_by_location)

    t1 = time.time()
    print(f'Scrape took {t1-t0} seconds')
    print(TipperScraper.total_tries)
    print()

main()
