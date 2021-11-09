import json
import os
import errno
from datetime import datetime, date
from typing import Any, Dict, List, Set, Union, cast
from session_time_filter import SessionTimeFilter

from tennis_clubs.tennis_court_session import TennisCourtSession
from tennis_clubs.lookahead_mapper import LookaheadMapper
from tipper_scraper import TipperScraper

from program_args import get_args

class TennisClub:
    def __init__(self, tennis_court_config: Dict[str, Any], session_time_filter: SessionTimeFilter) -> None:
        self.name: str = cast(str, tennis_court_config['name'])
        self._id: int = cast(int, tennis_court_config['court_id'])
        self._base_url: str = cast(str, tennis_court_config['base_url'])
        self._cache_path: str = os.path.join(os.path.dirname(__file__), '..', "cache", f"{self.name.lower().replace(' ', '_')}.json")
        self._court_number_offset: int = cast(int, tennis_court_config.get('court_number_offset', 0))
        self._book_on_hour: bool = cast(bool, tennis_court_config.get('book_on_hour', False))
        self._notify_on_new: bool = cast(bool, tennis_court_config.get('notify_on_new', False))
        self._base_schedule_url: str = self._get_url_from_endpoint(cast(str, tennis_court_config['schedule_endpoint']))
        self._current_sessions_by_date: Dict[date, Set[TennisCourtSession]] = {}
        self._newest_sessions_by_date: Dict[date, Set[TennisCourtSession]] = {}
        self._session_time_filter: SessionTimeFilter = session_time_filter
        self._lookahead_period_fetcher: LookaheadMapper = LookaheadMapper(cast(Dict[str, Union[str, int]], tennis_court_config['lookahead_strategy']))

        self.deserialize(self._load_json_from_path(self._cache_path))

    def deserialize(self, tennis_time_data: Dict[str, List[List[Union[str, int]]]]) -> None:
        for date_str, tennis_sessions_data in tennis_time_data.items():
            tennis_date: date = datetime.strptime(date_str, '%x').date()
            if tennis_date < datetime.now().date():
                continue

            tennis_sessions: Set[TennisCourtSession] = set()
            for tennis_session_data in tennis_sessions_data:
                tennis_sessions.add(TennisCourtSession.deserialize(tennis_session_data))
            self._current_sessions_by_date[tennis_date] = tennis_sessions

    def serialize(self) -> Dict[str, List[List[Union[str, int]]]]:
        tennis_time_data: Dict[str, List[List[Union[str, int]]]] = {}
        for date, tennis_sessions in self._current_sessions_by_date.items():
            tennis_sessions_data: List[List[Union[str, int]]] = []
            for tennis_session in tennis_sessions:
                tennis_sessions_data.append(tennis_session.serialize())
            tennis_time_data[date.strftime('%x')] = tennis_sessions_data
        return tennis_time_data

    def fetch_newest_tennis_times(self) -> bool:
        latest_tee_time: datetime = datetime.now()
        self._newest_sessions_by_date = {}
        for latest_tee_time in self._lookahead_period_fetcher.get_lookahead_days():
            date_str: str = self._get_date_str(latest_tee_time)
            session_times_data: List[Dict[str, Union[str, int, datetime]]] = TipperScraper.get_tennis_times_for_date(self._base_schedule_url.format(date_str), latest_tee_time, self._session_time_filter, self._book_on_hour)
            if session_times_data:
                session_times_for_day: Set[TennisCourtSession] = self._decorate_tee_time_data(session_times_data)
                new_session_times: Set[TennisCourtSession] = session_times_for_day - self._current_sessions_by_date.get(latest_tee_time.date(), set())
                if new_session_times:
                    self._newest_sessions_by_date[latest_tee_time.date()] = new_session_times
                self._current_sessions_by_date[latest_tee_time.date()] = session_times_for_day

        self._save_to_json_to_path(self.serialize(), self._cache_path)

        return len(self._newest_sessions_by_date) > 0 and self._notify_on_new

    def get_all_tennis_times_sorted(self) -> Dict[date, List[TennisCourtSession]]:
        tennis_times_sorted: Dict[date, List[TennisCourtSession]] = {}
        for tennis_date, sessions in self._current_sessions_by_date.items():
            tennis_times_sorted[tennis_date] = sorted(sessions, key=lambda x: x.start_time)

        return tennis_times_sorted

    def get_newest_tennis_sessions_sorted(self) -> Dict[date, List[TennisCourtSession]]:
        newest_times_sorted: Dict[date, List[TennisCourtSession]] = {}
        for tennis_date, sessions in self._newest_sessions_by_date.items():
            newest_times_sorted[tennis_date] = sorted(sessions, key=lambda x: x.start_time)

        return newest_times_sorted

    def get_schedule_url(self, booking_date: date) -> str:
        return self._base_schedule_url.format(self._get_date_str(booking_date))

    def _decorate_tee_time_data(self, tee_times_data: List[Dict[str, Union[str, int, datetime]]]) -> Set[TennisCourtSession]:
        tee_time_groups: Set[TennisCourtSession] = set()
        for tee_time_data in tee_times_data:
            tee_time_groups.add(TennisCourtSession(cast(datetime, tee_time_data['start_time']), cast(int, tee_time_data['court']) - self._court_number_offset, self._base_url + cast(str, tee_time_data['endpoint'])))
        return tee_time_groups

    def _get_url_from_endpoint(self, schedule_endpoint: str) -> str:
        return self._base_url + schedule_endpoint.format(self._id, "{}")

    def _get_date_str(self, date: date) -> str:
        return f'{date.year}-{date.month:02d}-{date.day:02d}'

    def _load_json_from_path(self, file_path: str) -> Any:
        if not os.path.exists(file_path) \
                or get_args().no_cache \
                or os.path.getsize(file_path) == 0:
            return {}

        with open(file_path, 'r') as f:
            return json.load(f)

    def _save_to_json_to_path(self, data: Any, file_path: str) -> None:
        if not os.path.exists(os.path.dirname(file_path)):
            try:
                os.makedirs(os.path.dirname(file_path))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

        with open(file_path, 'w') as f:
            json.dump(data, f)