from typing import Any, Dict, List
from datetime import datetime, time, timedelta

class SessionTimeFilter:
    def __init__(self, valid_times_config: List[Dict[str, str]]) -> None:
        self.valid_times_by_week: List[Dict[time, bool]] = self._initialize_valid_times_by_week(valid_times_config)

    def is_start_time_valid(self, session_start_time: datetime) -> bool:
        weekday_index: int = session_start_time.weekday()
        changing_time_keys: List[time] = list(self.valid_times_by_week[weekday_index].keys())
        if not changing_time_keys:
            return True

        i: int = self._binary_search(changing_time_keys, session_start_time.time())

        if i == -1:
            first_key: time = changing_time_keys[0]
            return not self.valid_times_by_week[weekday_index][first_key]
        else:
            return self.valid_times_by_week[weekday_index][changing_time_keys[i]]

    def _binary_search(self, arr: List[time], x: time) -> int:
        left: int = 0
        right: int = len(arr) - 1
        while left <= right:
            mid = left + (right - left) // 2
            if x > arr[mid]:
                left = mid + 1
            elif x < arr[mid]:
                right = mid - 1
            else:
                return mid
        return right

    def _initialize_valid_times_by_week(self, time_filter_configs: List[Dict[str, str]]) -> List[Dict[time, bool]]:
        time_filters_by_day: List[Dict[time, bool]] = [{} for _ in range(7)]
        for filter_config in time_filter_configs:
            for day_to_apply in self._get_applicable_days(filter_config['time_of_week']):
                if 'start' in filter_config:
                    start_time: datetime = datetime.strptime(filter_config['start'], '%I:%M%p')
                    time_filters_by_day[day_to_apply][start_time.time()] = True
                if 'end' in filter_config:
                    end_time: datetime = datetime.strptime(filter_config['end'], '%I:%M%p') + timedelta(minutes=1)
                    time_filters_by_day[day_to_apply][end_time.time()] = False

        return [dict(sorted(time_filters_by_day[i].items())) for i in range(7)]

    def _get_applicable_days(self, time_of_week: str) -> List[int]:
        if time_of_week == 'all':
            return [i for i in range(7)]
        elif time_of_week == 'weekend':
            return [5, 6]
        elif time_of_week == 'weekday':
            return [i for i in range(5)]

        return []