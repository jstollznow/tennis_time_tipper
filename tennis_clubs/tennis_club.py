import json
import os
import errno

from tennis_clubs.tennis_court_session import TennisCourtSession
from tipper_scraper import TipperScraper
from datetime import datetime, timedelta

from program_args import get_args

class TennisClub:
    def __init__(self, tennis_court_config) -> None:
        self.name = tennis_court_config['name']
        self.__id = tennis_court_config['court_id']
        self.__base_url = tennis_court_config['base_url']
        self.__cache_path = os.path.join(os.path.dirname(__file__), '..', "cache", f"{self.name.lower().replace(' ', '_')}.json")
        self.__lookahead_days = tennis_court_config.get('lookahead_days', 14)
        self.__court_number_offset = tennis_court_config.get('court_number_offset', 0)
        self.__book_on_hour = tennis_court_config.get('book_on_hour', False)
        self.__base_schedule_url = self.__get_url_from_endpoint(tennis_court_config['schedule_endpoint'])
        self.__tennis_session_times_by_date = {}

        self.deserialize(self.__load_json_from_path(self.__cache_path))

    def deserialize(self, tennis_time_data):
        for date_str, tennis_sessions_data in tennis_time_data.items():
            tennis_sessions = set()
            date = datetime.strptime(date_str, '%x').date()
            for tennis_session_data in tennis_sessions_data:
                tennis_sessions.add(TennisCourtSession.deserialize(tennis_session_data, self.__base_url))
            self.__tennis_session_times_by_date[date] = tennis_sessions

    def serialize(self):
        tennis_time_data = {}
        for date, tennis_sessions in self.__tennis_session_times_by_date.items():
            tennis_sessions_data = []
            for tennis_session in tennis_sessions:
                tennis_sessions_data.append(tennis_session.serialize())
            tennis_time_data[date.strftime('%x')] = tennis_sessions_data
        return tennis_time_data

    def get_new_tee_times_for_period(self, min_spots):
        latest_tee_time = datetime.now()
        new_tee_times_for_period = {}

        for latest_tee_time in self.__get_lookahead_cutoff_times():
            date_str = f'{latest_tee_time.year}-{latest_tee_time.month:02d}-{latest_tee_time.day:02d}'

            session_times_data = TipperScraper.get_tennis_times_for_date(self.__base_schedule_url.format(date_str), latest_tee_time, min_spots, self.__book_on_hour)
            if session_times_data:
                session_times_for_day = self.__decorate_tee_time_data(session_times_data)
                new_session_times = session_times_for_day - self.__tennis_session_times_by_date.get(latest_tee_time.date(), set())
                if new_session_times:
                    new_tee_times_for_period[latest_tee_time.date()] = sorted(new_session_times, key=lambda x: x.start_time)
                self.__tennis_session_times_by_date[latest_tee_time.date()] = session_times_for_day

        self.__save_to_json_to_path(self.serialize(), self.__cache_path)
        return new_tee_times_for_period

    def __decorate_tee_time_data(self, tee_times_data):
        tee_time_groups = set()
        for tee_time_data in tee_times_data:
            tee_time_groups.add(TennisCourtSession(tee_time_data['start_time'], tee_time_data['court'] - self.__court_number_offset, self.__base_url + tee_time_data['endpoint']))
        return tee_time_groups

    def __get_lookahead_cutoff_times(self):
        cutoff_times = []
        latest_tee_time = datetime.now()

        for _ in range(self.__lookahead_days):
            latest_tee_time += timedelta(1)
            cutoff_times.append(datetime.combine(latest_tee_time.date(), datetime.now().time()))
        return cutoff_times

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