# Calendar Analytics #

Calendar Analytics is a simple data visualization app for Google Calendar, created for the LSA Dean. It groups Google Calendar events according to event color, and generates a doughnut chart using the summed durations of each event color within a given date range.

#+html: <p align="center"><img src="https://github.com/GhastlyParadox/ghastlyparadox.github.io/blob/master/chart.jpeg" /></p>

## Technologies
- Python, OAuth 2.0, Google Calendar & People APIs, Flask, Jinja2, Datetime
- Javascript, jQuery, AJAX, D3, Chart.js, Underscore.js, Moment.js
- PostgreSQL, SQLAlchemy, HTML5, CSS, Bootstrap

## Installation

Requirements:

- Install PostgreSQL
- Python 2.6 or greater
- A Google Calendar account

Clone repository
```
$ git clone https://gitlab.umich.edu/lsa-ts-rsp/dean-calendar-tool.git
```
Create a virtual environment
```
$ python -m venv /path/to/new/virtual/environment
```
Activate the virtual environment
```
$ source env/bin/activate
```
Install dependencies
```
$ pip install -r requirements.txt
```
Create a project in the [Google Developers Console](https://console.developers.google.com/apis/api/calendar-json.googleapis.com/overview) and enable the Google Calendar and Google People APIs.

Create a secrets.sh file
```
$ touch secrets.sh
```
Add your flask app key to the secrets file
```
export FLASK_APP_KEY="flask_app_key_here"
```
Add your OAuth client id and client secret to the secrets file
```
export CLIENT_ID="client_id_here"
export CLIENT_SECRET="client_secret_here"
```
Load your secrets file into your environment
```
$ source secrets.sh
```
Run PostgreSQL and create a database with the name 'cals'
```
$ createdb cals
```
Run the app locally
```
$ python server.py
```
Go to localhost and login
