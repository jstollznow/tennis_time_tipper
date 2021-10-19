from datetime import datetime, timedelta
from typing import Dict, Union

class LookaheadMapper:
    NUM_OF_MONTHS = 12

    def __init__(self, lookahead_config: Dict[str, Union[str, int]]) -> None:
        self._lookahead_period = []
        self._set_days_in_period(lookahead_config.get('type', 'days'), lookahead_config.get('value', 14))

    def _set_days_in_period(self, type, value):
        cutoff_date: datetime = datetime.now()
        value += 1
        if type == 'days':
            cutoff_date += timedelta(days=value)
        elif type == 'months':
            carry = 0
            cutoff_month = cutoff_date.month + value
            if cutoff_month > LookaheadMapper.NUM_OF_MONTHS:
                carry = 1
                cutoff_month %= LookaheadMapper.NUM_OF_MONTHS
            cutoff_date = cutoff_date.replace(day=1, month=cutoff_month, year=cutoff_date.year + carry)
        elif type == 'weeks':
            cutoff_date += timedelta(days=-cutoff_date.weekday() + value * 7)

        working_date = datetime.now()

        while working_date < cutoff_date:
            self._lookahead_period.append(working_date)
            working_date += timedelta(days=1)

    def get_lookahead_days(self):
        return self._lookahead_period