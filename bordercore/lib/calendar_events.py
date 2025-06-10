from datetime import datetime, timedelta

import dateutil.parser
import httplib2
from apiclient.discovery import build
from oauth2client.client import OAuth2Credentials
from rfc3339 import datetimetostr
from rfc3339 import now as now_rfc3339

from accounts.models import UserProfile

api_key = ""


class Calendar():

    credentials = None

    def __init__(self, user_profile):
        if not isinstance(user_profile, UserProfile):
            raise ValueError("Calendar must be passed a UserProfile instance")
        cal_info = user_profile.google_calendar
        if cal_info:
            credentials = OAuth2Credentials(
                cal_info["access_token"],
                cal_info["client_id"],
                cal_info["client_secret"],
                cal_info["refresh_token"],
                cal_info["token_expiry"],
                cal_info["token_uri"],
                cal_info["user_agent"],
                cal_info["revoke_uri"],
                cal_info["id_token"],
                cal_info["token_response"],
            )
            self.credentials = credentials

    def has_credentials(self):
        return bool(self.credentials)

    def get_calendar_info(self):
        http = httplib2.Http()
        http = self.credentials.authorize(http)
        service = build(serviceName="calendar", version="v3", http=http, developerKey=api_key, cache_discovery=False)
        time_max = datetime.now() + timedelta(days=7)

        events = service.events().list(calendarId="bordercore@gmail.com",
                                       orderBy="startTime",
                                       singleEvents=True,
                                       timeMin=str(now_rfc3339()).replace(" ", "T"),
                                       timeMax=datetimetostr(time_max)).execute()
        event_list = []
        count = 1
        for e in events["items"]:
            one_event = {"count": count}
            for field in ["description", "location", "summary"]:
                try:
                    one_event[field] = e[field]
                except KeyError:
                    pass
            try:
                one_event["start_raw"] = e["start"]["dateTime"]
                one_event["start_pretty"] = dateutil.parser.parse(e["start"]["dateTime"]).strftime("%a %I:%M%p")
                one_event["end_raw"] = e["end"]["dateTime"]
                one_event["end_pretty"] = dateutil.parser.parse(e["end"]["dateTime"]).strftime("%a %I:%M%p")
            except KeyError:
                one_event["start_raw"] = e["start"]["date"]
                one_event["start_pretty"] = dateutil.parser.parse(e["start"]["date"]).strftime("%a %I:%M%p")
                one_event["end_raw"] = e["end"]["date"]
                one_event["end_pretty"] = dateutil.parser.parse(e["end"]["date"]).strftime("%a %I:%M%p")
            event_list.append(one_event)
            count = count + 1

        return event_list
