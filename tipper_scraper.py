import time
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

class TipperScraper:
    AVAILABLE_CLASS = ''
    AVAILABLE_TAG = ''
    TIME_OBJECT = ''
    AVAILABLE_SLOT = ''

    TIMETABLE_ENDPOINT = ''
    ADD_TO_CART_ENDPOINT = ''
    CHECKOUT_ENDPOINT = ''

    __request_session = None
    total_tries = 0
    SESSION_LENGTH = 30

    @staticmethod
    def set_scraping_details(xml_config):
        TipperScraper.AVAILABLE_CLASS = xml_config['AVAILABLE_CLASS']
        TipperScraper.AVAILABLE_TAG = xml_config['AVAILABLE_TAG']
        TipperScraper.__request_session = requests.session()

    @staticmethod
    def get_tennis_times_for_date(schedule_url, tee_time_cut_off, min_spots, book_on_hour):
        tennis_times = []
        tennis_start_times = {}
        soup = BeautifulSoup(TipperScraper.__get_content(schedule_url), features="lxml")
        for row in soup.find_all(TipperScraper.AVAILABLE_TAG, TipperScraper.AVAILABLE_CLASS):
            tennis_court_regex = re.search(r"'(.*start=([0-9:]+).*court=([0-9]+))", row.get('href'))
            if tennis_court_regex:
                session_start_time = datetime.combine(tee_time_cut_off.date(), datetime.strptime(tennis_court_regex.group(2), '%H:%M').time())
                court_number = int(tennis_court_regex.group(3))
                new_session_key = f"{session_start_time.strftime('%H:%M')}-{court_number}"
                new_session = {
                    'start_time': session_start_time,
                    'court': court_number,
                    'endpoint': '/' + tennis_court_regex.group(1)
                }

                if book_on_hour:
                    tennis_times.append(new_session)
                    continue

                tennis_start_times[new_session_key] = new_session
                session_before_key = f"{(session_start_time - timedelta(minutes=TipperScraper.SESSION_LENGTH)).strftime('%H:%M')}-{court_number}"

                if session_before_key in tennis_start_times:
                    tennis_times.append(tennis_start_times[session_before_key])
                    del tennis_start_times[session_before_key]
            else:
                print('No match! For', row)
        return tennis_times

    @staticmethod
    def __get_content(url):
        resp_status_code = 403
        while resp_status_code == 403:
            response = TipperScraper.__request_session.get(url)
            resp_status_code = response.status_code
            TipperScraper.total_tries += 1
            # time.sleep(0.1)
        return response.text