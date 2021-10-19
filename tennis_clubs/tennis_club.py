import json
import os
import errno
from datetime import datetime

from tennis_clubs.tennis_court_session import TennisCourtSession
from tennis_clubs.lookahead_mapper import LookaheadMapper
from tipper_scraper import TipperScraper

from program_args import get_args

class TennisClub:
    def __init__(self, tennis_court_config, session_time_filter) -> None:
        self.name = tennis_court_config['name']
        self.__id = tennis_court_config['court_id']
        self.__base_url = tennis_court_config['base_url']
        self.__cache_path = os.path.join(os.path.dirname(__file__), '..', "cache", f"{self.name.lower().replace(' ', '_')}.json")
        self.__court_number_offset = tennis_court_config.get('court_number_offset', 0)
        self.__book_on_hour = tennis_court_config.get('book_on_hour', False)
        self.__base_schedule_url = self.__get_url_from_endpoint(tennis_court_config['schedule_endpoint'])
        self._tennis_session_times_by_date = {}
        self.__session_time_filter = session_time_filter
        self.__lookahead_period_fetcher = LookaheadMapper(tennis_court_config['lookahead_strategy'])
        self.newest_tee_times = {}

        self.deserialize(self.__load_json_from_path(self.__cache_path))

    def deserialize(self, tennis_time_data):
        for date_str, tennis_sessions_data in tennis_time_data.items():
            tennis_sessions = set()
            date = datetime.strptime(date_str, '%x').date()
            for tennis_session_data in tennis_sessions_data:
                tennis_sessions.add(TennisCourtSession.deserialize(tennis_session_data))
            self._tennis_session_times_by_date[date] = tennis_sessions

    def serialize(self):
        tennis_time_data = {}
        for date, tennis_sessions in self._tennis_session_times_by_date.items():
            tennis_sessions_data = []
            for tennis_session in tennis_sessions:
                tennis_sessions_data.append(tennis_session.serialize())
            tennis_time_data[date.strftime('%x')] = tennis_sessions_data
        return tennis_time_data

    def get_new_tee_times_for_period(self) -> bool:
        latest_tee_time = datetime.now()
        self.newest_tee_times = {}

        for latest_tee_time in self.__lookahead_period_fetcher.get_lookahead_days():
            date_str = f'{latest_tee_time.year}-{latest_tee_time.month:02d}-{latest_tee_time.day:02d}'
            session_times_data = TipperScraper.get_tennis_times_for_date(self.__base_schedule_url.format(date_str), latest_tee_time, self.__session_time_filter, self.__book_on_hour)
            if session_times_data:
                session_times_for_day = self.__decorate_tee_time_data(session_times_data)
                new_session_times = session_times_for_day - self._tennis_session_times_by_date.get(latest_tee_time.date(), set())
                if new_session_times:
                    self.newest_tee_times[latest_tee_time.date()] = sorted(new_session_times, key=lambda x: x.start_time)
                self._tennis_session_times_by_date[latest_tee_time.date()] = session_times_for_day

        self.__save_to_json_to_path(self.serialize(), self.__cache_path)

        return self.newest_tee_times

    def get_all_tee_times_sorted(self):
        tee_times_for_period = {}
        for date, sessions in self._tennis_session_times_by_date.items():
            tee_times_for_period[date] = sorted(sessions, key=lambda x: x.start_time)

        return tee_times_for_period

    def __decorate_tee_time_data(self, tee_times_data):
        tee_time_groups = set()
        for tee_time_data in tee_times_data:
            tee_time_groups.add(TennisCourtSession(tee_time_data['start_time'], tee_time_data['court'] - self.__court_number_offset, self.__base_url + tee_time_data['endpoint']))
        return tee_time_groups

    def __get_url_from_endpoint(self, schedule_endpoint):
        return self.__base_url + schedule_endpoint.format(self.__id, "{}")

    def __load_json_from_path(self, file_path):
        if not os.path.exists(file_path) \
                or get_args().no_cache \
                or os.path.getsize(file_path) == 0:
            return {}

        with open(file_path, 'r') as f:
            return json.load(f)

    def __save_to_json_to_path(self, data, file_path):
        if not os.path.exists(os.path.dirname(file_path)):
            try:
                os.makedirs(os.path.dirname(file_path))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        with open(file_path, 'w') as f:
            json.dump(data, f)