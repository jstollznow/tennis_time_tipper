from __future__ import annotations
from datetime import datetime
from typing import List, Union, cast

class TennisCourtSession:
    def __init__(self, start_time: datetime, court: int, booking_url: str) -> None:
        self.start_time = start_time
        self.court_number = court
        self.booking_url = booking_url

    @staticmethod
    def deserialize(serialized_data: List[Union[str, int]]) -> TennisCourtSession:
        return TennisCourtSession(datetime.strptime(cast(str, serialized_data[0]), '%c'), cast(int, serialized_data[1]), cast(str, serialized_data[2]))

    def serialize(self) -> List[Union[str, int]]:
        return [self.start_time.strftime('%c'), self.court_number, self.booking_url]

    def get_time_str(self) -> str:
        return self.start_time.strftime('%I:%M %p')

    def __eq__(self, o: object) -> bool:
        return self.__hash__() == o.__hash__()

    def __hash__(self) -> int:
        return hash((self.start_time, self.court_number))