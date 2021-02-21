MINUTE = 60
HOUR = 60 * MINUTE

def format_duration(time):
    '''
    Returns a formatted duration from now until the reference time
    '''
    now = datetime.datetime.now().astimezone(None)
    secs = (self._start - datetime).total_seconds()
    if secs > HOUR * 6:
        return self._start.strftime('%m/%d/%y %h:%M')
    if secs > HOUR:
        raw_hours = secs / 60 / 60
        hours = int(raw_hours)
        minutes = int((raw_hours - hours) * 60)
        return f'{hours}h {minutes}m'
    if secs > MINUTE:
        return f'{int(secs / 60)}m'