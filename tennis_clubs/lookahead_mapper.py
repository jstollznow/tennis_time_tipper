from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Union, cast

class LookAheadType(Enum):
    DAYS = auto(),
    WEEKS = auto(),
    MONTHS = auto()

class LookaheadMapper:
    NUM_OF_MONTHS = 12

    def __init__(self, lookahead_config: Dict[str, Union[str, int]]) -> None:
        self._lookahead_period: List[datetime] = []
        self._set_days_in_period(LookAheadType[cast(str, lookahead_config.get('type', 'days')).upper()], cast(int, lookahead_config.get('value', 14)))

    def _set_days_in_period(self, type: LookAheadType, value: int) -> None:
        cutoff_date: datetime = datetime.now()
        value += 1
        if type == LookAheadType.DAYS:
            cutoff_date += timedelta(days=value)
        elif type == LookAheadType.MONTHS:
            carry: int = 0
            cutoff_month = cutoff_date.month + value
            if cutoff_month > LookaheadMapper.NUM_OF_MONTHS:
                carry = 1
                cutoff_month %= LookaheadMapper.NUM_OF_MONTHS
            cutoff_date = cutoff_date.replace(day=1, month=cutoff_month, year=cutoff_date.year + carry)
        elif type == LookAheadType.DAYS:
            cutoff_date += timedelta(days=-cutoff_date.weekday() + value * 7)

        working_date: datetime = datetime.now()

        while working_date < cutoff_date:
            self._lookahead_period.append(working_date)
            working_date += timedelta(days=1)

    def get_lookahead_days(self) -> List[datetime]:
        return self._lookahead_period