from datetime import datetime

class TennisCourtSession:
    def __init__(self, start_time, court, booking_url) -> None:
        self.start_time = start_time
        self.court_number = court
        self.booking_url = booking_url

    @staticmethod
    def deserialize(serialized_data, base_url):
        return TennisCourtSession(datetime.strptime(serialized_data[0], '%c'), serialized_data[1], base_url + serialized_data[2])

    def serialize(self):
        return [self.start_time.strftime('%c'), self.court_number, self.booking_url]

    def get_time_str(self):
        return self.start_time.strftime('%I:%M %p')

    def __eq__(self, o: object) -> bool:
        return self.__hash__() == o.__hash__()

    def __hash__(self) -> int:
        return hash((self.start_time, self.court_number))