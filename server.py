import os
from flask import Flask, session, render_template, request, redirect, url_for, jsonify
from jinja2 import StrictUndefined
import httplib2
from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets, OAuth2Credentials
from googleapiclient import sample_tools, discovery
from model import connect_to_db, Event, UserCal, CalEvent, db, User, Calendar
from datetime import datetime, timedelta
from seed import seed_user, seed_calendars, seed_events
import logging
import json
import itertools


class YourFlask(Flask):
    def create_jinja_environment(self):
        self.auto_reload = True
        self.config['TEMPLATES_AUTO_RELOAD'] = True
        return Flask.create_jinja_environment(self)

app = YourFlask(__name__)
app.config.update(DEBUG=True, SECRET_KEY=os.getenv("FLASK_KEY"), TEMPLATE_FOLDER="/templates/")


@app.route('/')
def login():
    """Renders login page"""

    return render_template("login.html")


@app.route("/oauth2callback")
def oauth2callback():
    """Authenticates google user and authorizes app"""

    logging.basicConfig(filename='debug.log', level=logging.WARNING)

    flow = flow_from_clientsecrets(
                  'client_secret.json',
                  scope='https://www.googleapis.com/auth/calendar.readonly \
                  https://www.googleapis.com/auth/plus.login',
                  redirect_uri=url_for('oauth2callback', _external=True))

    flow.params['access_type'] = 'online'
    flow.params['approval_prompt'] = 'auto'

    if 'code' not in request.args:
        auth_uri = flow.step1_get_authorize_url()
        return redirect(auth_uri)

    else:
        auth_code = request.args.get('code')
        credentials = flow.step2_exchange(auth_code)  # creates credentials object
        session['credentials'] = credentials.to_json()
        return redirect(url_for('oauth2'))


@app.route('/oauth2')
def oauth2():
    """Builds API service objects,
    makes API calls, and seeds db"""

    if 'credentials' not in session:
        return redirect(url_for('oauth2callback'))
    credentials = pull_credentials()

    if credentials.access_token_expired:
        return redirect(url_for('oauth2callback'))
    else:
        http_auth = credentials.authorize(httplib2.Http())
        people_service, calendar_service, event_service = get_service_objects(http_auth)

    create_user_id()

    profile = profile_api_call(people_service)

    now, two_months, two_months_back = get_dates()

    primary_calendar = calendar_service.calendarList().get(calendarId='primary').execute()
    dean_calendar = calendar_service.calendarList().get(calendarId='laneag@gmail.com').execute()
    calendars = { primary_calendar['id'] : primary_calendar, dean_calendar['id'] : dean_calendar}
    colors = calendar_service.colors().get().execute()                                                                #for event colors/labels
    events = event_api_call(event_service,
                             calendar_service,
                             calendars)

    calendar_colors = { "primary" : primary_calendar['backgroundColor'], "dean" : dean_calendar['backgroundColor'] }  #Calendar colors for default-colored events

    # database seed
    seed_db(profile, calendars, events, colors, calendar_colors)

    return redirect("/dashboard")


@app.route('/dashboard')
def dashboard():
    """Renders list of calendar options on dashboard page"""

    calendar_options = get_calendar_options()
    calendar_options = sorted(calendar_options)

    return render_template('dashboard.html',
                           calendar_options=calendar_options)


@app.route('/doughnut.json')
def doughnut():
    """Receives data from ajax request,
    jsonifies object to send to client."""

    selected_calendar = request.args.get('calendar')
    startdate = request.args.get('startdate')
    enddate = request.args.get('enddate')

    startdate = to_datetime(startdate)
    enddate = to_datetime(enddate)

    events = get_event_type(selected_calendar, startdate, enddate)
    labels_and_durations = total_durations(events)
    data = doughnut_data(labels_and_durations)

    return jsonify(data)


@app.route('/logout')
def logout():
    """On logout, revokes oauth credentials,
       and deletes them from the session"""

    credentials = pull_credentials()
    credentials.revoke(httplib2.Http())  # for demo purposes
    del session['credentials']
    del session['sub']

    return redirect("/")


def pull_credentials():
    """Pulls credentials out of session"""

    return OAuth2Credentials.from_json(session['credentials'])


def create_user_id():
    """Adds google id_token to session"""

    cred_dict = json.loads(session['credentials'])
    user_id = cred_dict['id_token']['sub']
    session['sub'] = user_id


def get_service_objects(http_auth):
    """Builds google API service objects"""

    people_service = discovery.build('people', 'v1', http_auth, cache_discovery=False)
    calendar_service = discovery.build('calendar', 'v3', http_auth, cache_discovery=False)
    event_service = discovery.build('calendar', 'v3', http_auth, cache_discovery=False)


    return people_service, calendar_service, event_service


def get_dates():
    """Creates datetime variables for events API call"""

    now = datetime.utcnow().isoformat() + 'Z'

    two_months = datetime.now() + timedelta(weeks=8)
    two_months = two_months.isoformat() + 'Z'

    two_months_back = datetime.now() - timedelta(weeks=8)
    two_months_back = two_months_back.isoformat() + 'Z'

    return now, two_months, two_months_back


def calendar_api_call(calendar_service):
    """Executes google calendar api call"""

    return calendar_service.calendarList().get(calendarId='primary').execute()


def profile_api_call(people_service):
    """Executes google people api call"""

    return people_service.people().get(resourceName='people/me', personFields='names').execute()


def event_api_call(event_service, calendar_service, calendars):
    """Executes paginated API calls for each calendar"""

    events = {}

    now, two_months, two_months_back = get_dates()

    for calendar_id in calendars:

        requests = {}
        events_call = event_service.events().list(calendarId=calendar_id,
                                              timeMin=two_months_back,
                                              timeMax=two_months,
                                              maxResults = 1500,
                                              singleEvents=True,
                                              orderBy='startTime')

        while events_call:
            response = events_call.execute()
            requests.update(response)
            events_call = event_service.events().list_next(events_call, response)

        events[calendar_id] = requests

    return events


def get_user_id():
    """Returns user_id"""

    return session['sub']


def seed_db(profile_result, calendars, events, colors, calendar_colors):
    """Seeds db"""

    user_id = get_user_id()

    seed_user(profile_result, user_id)
    seed_calendars(calendars, user_id)
    seed_events(events, colors, calendar_colors)


def get_calendar_options():
    """Queries db for users's list of shared calendars"""

    user_id = get_user_id()

    calendars = UserCal.query.filter_by(user_id=user_id).all()
    calendar_options = []

    for cal in calendars:
        calendar_options.append(cal.calendar_id)

    return calendar_options


def to_datetime(str_date):
    """Converts string to datetime object"""

    return datetime.strptime(str_date, "%m/%d/%Y")


def get_event_type(selected_calendar, startdate, enddate):
    """Queries db for selected calendar's event types
    and durations."""

    events = []
    evts = db.session.query(CalEvent, Event).join(Event).all()

    for calevent, event in evts:
        if selected_calendar.lower() in calevent.calendar_id and event.start > startdate and event.end < enddate:
            events.append(event)

    return events


def total_durations(events):
    """Creates a dictionary of the total duration of
    all events in each color/category."""

    labels_and_durations = {}
    labels_and_colors = {}

    for event in events:
        if event.duration_minutes > 720:            #Skip all day events
            continue
        else:
            labels_and_durations.setdefault(event.label, 0)
            labels_and_durations[event.label] += event.duration_minutes

            labels_and_colors.setdefault(event.label, 0)
            labels_and_colors[event.label] = event.color

    labels_and_durations = [labels_and_durations, labels_and_colors]

    return labels_and_durations


def doughnut_data(labels_and_durations):
    """Creates an object of three lists to generate the doughnut chart"""

    labels = [key for key in labels_and_durations[0].keys()]
    durations = [value for value in labels_and_durations[0].values()]
    colors = [value for value in labels_and_durations[1].values()]

    data = {"durations": durations, "labels": labels, "colors": colors}


    return data


if __name__ == "__main__":

    connect_to_db(app)
    app.run()
