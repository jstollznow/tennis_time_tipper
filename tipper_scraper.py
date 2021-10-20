import time
import re
from typing import Dict, List, Match, Optional, Union
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from requests.models import Response

from requests.sessions import Session

from session_time_filter import SessionTimeFilter

class TipperScraper:
    AVAILABLE_CLASS: str = ''
    AVAILABLE_TAG: str = ''
    TIME_OBJECT: str = ''
    AVAILABLE_SLOT: str = ''

    TIMETABLE_ENDPOINT: str = ''
    ADD_TO_CART_ENDPOINT: str = ''
    CHECKOUT_ENDPOINT: str = ''

    _request_session: Optional[Session] = None
    _total_tries: int = 0
    _session_length: int = 30

    @staticmethod
    def set_scraping_details(xml_config) -> None:
        TipperScraper.AVAILABLE_CLASS = xml_config['AVAILABLE_CLASS']
        TipperScraper.AVAILABLE_TAG = xml_config['AVAILABLE_TAG']
        TipperScraper._request_session = requests.session()

    @staticmethod
    def get_tennis_times_for_date(
            schedule_url: str,
            tee_time_cut_off: datetime,
            session_time_validator: SessionTimeFilter,
            book_on_hour: bool) -> List[Dict[str, Union[str, int, datetime]]]:
        tennis_times: List[Dict[str, Union[str, int, datetime]]] = []
        tennis_start_times: Dict[str, Dict[str, Union[str, int, datetime]]] = {}
        soup = BeautifulSoup(TipperScraper._get_content(schedule_url), features="lxml")
        for row in soup.find_all(TipperScraper.AVAILABLE_TAG, TipperScraper.AVAILABLE_CLASS):
            tennis_court_regex: Optional[Match] = re.search(r"'(.*start=([0-9:]+).*court=([0-9]+))", row.get('href'))
            if tennis_court_regex:
                session_start_time: datetime = datetime.combine(tee_time_cut_off.date(), datetime.strptime(tennis_court_regex.group(2), '%H:%M').time())
                is_valid_start_time: bool = session_time_validator.is_start_time_valid(session_start_time)
                court_number: int = int(tennis_court_regex.group(3))
                new_session_key: str = f"{session_start_time.strftime('%H:%M')}-{court_number}"
                new_session: Dict[str, Union[str, int, datetime]] = {
                    'start_time': session_start_time,
                    'court': court_number,
                    'endpoint': '/' + tennis_court_regex.group(1)
                }
                if book_on_hour and is_valid_start_time:
                    tennis_times.append(new_session)
                    continue
                if is_valid_start_time:
                    tennis_start_times[new_session_key] = new_session

                session_before_key: str = f"{(session_start_time - timedelta(minutes=TipperScraper._session_length)).strftime('%H:%M')}-{court_number}"
                if session_before_key in tennis_start_times:
                    tennis_times.append(tennis_start_times[session_before_key])
                    del tennis_start_times[session_before_key]
        return tennis_times

    @staticmethod
    def _get_content(url: str) -> str:
        if TipperScraper._request_session is None:
            return str()

        resp_status_code: int = 403
        while resp_status_code== 403:
            response: Response = TipperScraper._request_session.get(url)
            resp_status_code = response.status_code
            TipperScraper._total_tries += 1
            if resp_status_code == 403:
                time.sleep(0.1)

        return response.text