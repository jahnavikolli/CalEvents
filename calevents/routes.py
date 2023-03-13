import json
from datetime import datetime
from urllib import parse

from flask import jsonify, redirect, request, session, url_for
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from calevents import SCOPES, app, db
from calevents.models import Tokens


@app.route("/")
def hello():
    return "<ul><li>/listEvents: Lists events</li><li>/authorize: Generates auth token</li></ul>"

# Endpoint that will send authorization req to google oauth
@app.route("/authorize")
def authorize():
    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = Flow.from_client_secrets_file(
      "webservice-credentials.json", scopes=SCOPES)

    # The URI created here must exactly match one of the authorized redirect URIs
    # for the OAuth 2.0 client, which you configured in the API Console. If this
    # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
    # error.
    flow.redirect_uri = url_for('oauth2callback', _external=True)

    req_state = request.query_string.decode()

    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes='true',
        state=req_state,
        prompt='select_account'
    )

    session['state'] = state
    # redirect the request to oauth server
    return redirect(authorization_url)

# Endpoint that google oauth will call
@app.route('/oauth2callback')
def oauth2callback():
    print("in callback")
    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
    state = session['state']

    flow = Flow.from_client_secrets_file(
        "webservice-credentials.json", scopes=SCOPES, state=state)
    flow.redirect_uri = url_for('oauth2callback', _external=True)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Store credentials in the session.
    creds = flow.credentials

    qs = parse.parse_qs(request.args.get('state'))
    
    userid = qs['userid'][0]
    timemin = qs['timemin'][0]
    timemax = qs['timemax'][0]

    token = Tokens(userid=userid, token=creds.to_json())
    db.session.add(token)
    db.session.commit()

    # send request back to /listEvent
    return redirect(url_for('listEvent', userid=userid, timemin=timemin, timemax=timemax))

@app.route("/listEvents")
def listEvent():
    print("in listevents")
    
    userid = request.args.get('userid')
    timemin = request.args.get('timemin')
    timemax = request.args.get('timemax')
    nextPageToken = request.args.get('nextpagetoken')

    # Fail the request if arguments not found
    if userid is None or timemin is None or timemax is None:
        return "Userid, timemin, timemax expected", 400

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    
    # Get the token json string from db
    token_row = Tokens.query.filter_by(userid=userid).first()
    if token_row is not None:
        token_json = json.loads(token_row.token)
        creds = Credentials(
            token_json['token'], 
            refresh_token=token_json['refresh_token'],
            token_uri=token_json['token_uri'],
            client_id=token_json['client_id'],
            client_secret=token_json['client_secret'],
            scopes=token_json['scopes'],
            expiry=datetime.strptime(token_json['expiry'],'%Y-%m-%dT%H:%M:%S.%fZ')
        )
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            redirect_url = url_for("authorize", userid=userid, timemin=timemin, timemax=timemax, nextpagetoken=nextPageToken)
            # Redirect to authorization endpoint
            return redirect(redirect_url)

        # Save the credentials for the next run
        if token_row is None:
            token = Tokens(userid=userid, token=creds.to_json())
            db.session.add(token)
        else:
            token_row.token = creds.to_json()
        
        db.session.commit()

    try:
        service = build('calendar', 'v3', credentials=creds)

        # Call the Calendar API
        print('Getting the 10 events')
        events_result = service.events().list(calendarId='primary', timeMin=timemin,
                                              timeMax = timemax, maxResults=10, 
                                              singleEvents=True, orderBy='startTime',
                                              pageToken=nextPageToken).execute()
        events = events_result.get('items', [])
        nextPageToken = events_result.get('nextPageToken')

        if not events:
            print('No upcoming events found.')
            return

        # Create Ur own response
        res = {}
        res['nextPageToken'] = nextPageToken

        event_list = []
        # Prints the start and name of the next 10 events
        for event in events:
            myEvent = {}
            myEvent['end'] = event['end']
            myEvent['start'] = event['start']
            myEvent['summary'] = event['summary']
            

            event_list.append(myEvent)

        res['events'] = event_list

        return jsonify(res), 200

    except HttpError as error:
        print('An error occurred: %s' % error)
        return "HttpError", 500
