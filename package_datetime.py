from datetime import datetime, timezone, timedelta

#there are three class in datetime package timedelta, date, datetime, time
now = datetime.now()
now_timezone = datetime.now(tz=timezone.utc)
print(f'now: {now}')
print(f'now_timezone: {now_timezone}')

#convert datetime to formated string with method strftime
now_string = now.strftime("%B %d %Y")
print(f'now_string one: {now_string}')
now_string = now.strftime("%b %m %y")
print(f'now_string tow: {now_string}')

#convert string to datetime with strptime
second_datetime = datetime.strptime(now_string, "%b %m %y")
print(f'second_datetime type: {type(second_datetime)}')

#convert datetime to string with isoformat
datetime_isoformat = second_datetime.isoformat()
print(f'datetime_isoformat: {datetime_isoformat}')
datetime_isoformat = second_datetime.isoformat(sep=' ')
print(f'datetime_isoformat second: {datetime_isoformat}')

#datetime add
year_diff = timedelta(days=365) * 10
ten_year_from_now = now + year_diff
print('ten year from now: ', ten_year_from_now)

#we datetime we have method like strftime, strptime, fromisoformat, isoformat, 
