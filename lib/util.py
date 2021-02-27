import datetime
import typing
from threading import Timer
MINUTE = 60
HOUR = 60 * MINUTE


def format_duration(time: datetime.datetime) -> str:
    '''
    Returns a formatted duration from now until the reference time
    '''
    now = datetime.datetime.now().astimezone(None)
    secs = (time - now).total_seconds()
    if secs > HOUR * 6:
        return time.strftime('%-m/%-d/%y %-I:%M')
    if secs > HOUR:
        raw_hours = secs / 60 / 60
        hours = int(raw_hours)
        minutes = int((raw_hours - hours) * 60)
        return f'{hours}h {minutes}m'
    if secs > MINUTE:
        return f'{int(secs / 60)}m'


T = typing.TypeVar('T')
U = typing.TypeVar('U')


def safe_lookup(d: typing.Dict[T, U], key: T) -> typing.Optional[U]:
    try:
        return d[key]
    except KeyError:
        return None


def parse_datetime(s: str) -> datetime.datetime:
    return datetime.datetime.strptime(
        s,
        "%Y-%m-%dT%H:%M:%S%z"
    ).astimezone(None)
