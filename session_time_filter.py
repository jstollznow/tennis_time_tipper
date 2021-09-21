from datetime import datetime

class SessionTimeFilter:
    def __init__(self, valid_times_config) -> None:
        # self.id = round_type_config['id']
        # self.name = round_type_config['name']
        # self.type = TimeOfWeek[round_type_config.get('type', 'all').lower()]
        # self.round_fee_ids = [None for _ in range(7)]
        # self.__initialize_booking_ids(round_type_config['round_fee_ids'])
        # self.__base_booking_url = base_booking_url.format("{}", self.id)
        # self.__base_add_to_cart_url = base_add_to_cart_url.format("{}", self.id, "{}")
        # self.__tee_times_by_date = {}
        # self.booking_ids = {}

        self.valid_times_by_week = self.__initialize_valid_times_by_week(valid_times_config)

    def is_start_time_valid(self, session_start_time):
        weekday_index = session_start_time.weekday()
        changing_time_keys = list(self.valid_times_by_week[weekday_index].keys())
        if not changing_time_keys:
            return True

        time_key = self.__binary_search(changing_time_keys, session_start_time.time() , 0, len(changing_time_keys) - 1)

        if time_key == -1:
            first_key = changing_time_keys[0]
            return not self.valid_times_by_week[weekday_index][first_key]
        else:
            return self.valid_times_by_week[weekday_index][time_key]

    def __binary_search(self, values, target, left, right):
        if left > right:
            if left == 0:
                return -1
            return values[right]
        mid = int(left + (right - left) / 2)
        if target > values[mid]:
            return self.__binary_search(values, target, mid + 1, right)
        elif target < values[mid]:
            return self.__binary_search(values, target, left, mid - 1)
        else:
            return values[mid]

    def __initialize_valid_times_by_week(self, time_filter_configs):
        time_filters_by_day = [{} for _ in range(7)]
        for filter_config in time_filter_configs:
            for day_to_apply in self.__get_applicable_days(filter_config['time_of_week']):
                if 'start' in filter_config:
                    start_time = datetime.strptime(filter_config['start'], '%I:%M%p')
                    time_filters_by_day[day_to_apply][start_time.time()] = True
                if 'end' in filter_config:
                    end_time = datetime.strptime(filter_config['end'], '%I:%M%p')
                    time_filters_by_day[day_to_apply][end_time.time()] = False

        return [dict(sorted(time_filters_by_day[i].items())) for i in range(7)]

    def __get_applicable_days(self, time_of_week):
        if time_of_week == 'all':
            return [i for i in range(7)]
        elif time_of_week == 'weekend':
            return [5, 6]
        elif time_of_week == 'weekday':
            return [i for i in range(5)]

        return []