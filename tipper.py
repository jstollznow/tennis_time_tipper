from datetime import datetime
from typing import Dict, List
from session_time_filter import SessionTimeFilter
import time
import json

from tennis_clubs.tennis_club import TennisClub
from tipper_scraper import TipperScraper
from email_management.email_manager import EmailManager
from program_args import get_args

def main():
    with open(get_args().course_config_path) as f:
        tipper_config = json.load(f)

    TipperScraper.set_scraping_details(tipper_config['xml_objects'])

    tennis_courts: Dict[str, TennisClub] = {}
    session_filter: SessionTimeFilter = SessionTimeFilter(tipper_config['valid_times'])
    should_send_all: bool = tipper_config.get('send_all', False)

    for course_config in tipper_config['court_locations']:
        tennis_court: TennisClub = TennisClub(course_config, session_filter)
        tennis_courts[tennis_court.name] = tennis_court


    print('Getting new tennis times')
    print(datetime.now())
    new_tennis_time_locations: List[str] = []
    t0 = time.time()

    for tennis_court in tennis_courts.values():
        print(f'{tennis_court.name}')
        if tennis_court.fetch_newest_tennis_times():
            print(f'New times at {tennis_court.name}')
            new_tennis_time_locations.append(tennis_court.name)

    if new_tennis_time_locations:
        email_manager: EmailManager = EmailManager(get_args().local, tipper_config['email_details'])
        email_manager.create_and_send_email("new_tennis_times",
                new_tennis_sessions=new_tennis_time_locations,
                tennis_courts=tennis_courts,
                send_all=should_send_all)

    t1 = time.time()
    print(f'Scrape took {t1-t0} seconds')
    print(TipperScraper._total_tries)
    print()

main()
