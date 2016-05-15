from accounts.models import UserProfile
from oauth2client.client import OAuth2Credentials
from datetime import datetime, timedelta
from rfc3339 import now as now_rfc3339, datetimetostr
from apiclient.discovery import build
import httplib2
import dateutil.parser

api_key = ""


class Calendar():

    def __init__(self, user_profile):
        if not isinstance(user_profile, UserProfile):
            raise ValueError("Calendar must be passed a UserProfile instance")
        cal_info = user_profile.google_calendar
        self.calendar_id = cal_info['id']
        credentials = OAuth2Credentials(
            cal_info['credentials']['access_token'],
            cal_info['credentials']['client_id'],
            cal_info['credentials']['client_secret'],
            cal_info['credentials']['refresh_token'],
            cal_info['credentials']['token_expiry'],
            cal_info['credentials']['token_uri'],
            cal_info['credentials']['user_agent'],
            cal_info['credentials']['revoke_uri'],
            cal_info['credentials']['id_token'],
            cal_info['credentials']['token_response'],
        )
        self.credentials = credentials

    def get_calendar_info(self):
        http = httplib2.Http()
        http = self.credentials.authorize(http)
        service = build(serviceName='calendar', version='v3', http=http, developerKey=api_key)
        timeMax = datetime.now() + timedelta(days=7)

        events = service.events().list(calendarId=self.calendar_id,
                                       orderBy='startTime',
                                       singleEvents=True,
                                       timeMin=str(now_rfc3339()).replace(' ', 'T'),
                                       timeMax=datetimetostr(timeMax)).execute()
        event_list = []
        for e in events['items']:
            one_event = {}
            for field in ['description', 'location', 'summary']:
                try:
                    one_event[field] = e[field]
                except KeyError:
                    pass
            try:
                one_event['start_raw'] = e['start']['dateTime']
                one_event['start_pretty'] = dateutil.parser.parse(e['start']['dateTime']).strftime('%a %I:%M%p')
                one_event['end_raw'] = e['end']['dateTime']
                one_event['end_pretty'] = dateutil.parser.parse(e['end']['dateTime']).strftime('%a %I:%M%p')
            except KeyError:
                one_event['start_raw'] = e['start']['date']
                one_event['start_pretty'] = dateutil.parser.parse(e['start']['date']).strftime('%a %I:%M%p')
                one_event['end_raw'] = e['end']['date']
                one_event['end_pretty'] = dateutil.parser.parse(e['end']['date']).strftime('%a %I:%M%p')
            event_list.append(one_event)

        return event_list
