# CalEvents

A simple flask API to handle user authorization to list Calender events from a user's google calender. The endpoints in this API uses OAuth2 web application tokens from google's authentication library to 
- handle user authentication & authorization via consent pages 
- handle storing of tokens in a db and refreshing expired tokens
- validates requests received for proper format and send relevant error code

## API

- `GET /listEvents?userid=<uniqueUserID>&timemin=<Left Bound>&timemax=<Right Bound>&nextPageToken=<Optional page token>`
returns upto 10 events in the given time range in the following format
```json
{
    "events": [
        {
            "start": {
                "dateTime": "YYYY-MM-DDTHH:MM:SS.msZ",
                "timeZone": "<timezone>
            },
            "end": {
                "dateTime": "YYYY-MM-DDTHH:MM:SS.msZ",
                "timeZone": "<timezone>"
            },
            "summary": "<summary>"
        },
        {
            event 2 
        }
        ...
    ],
    "nextPageToken": "<Next Page Token>"
}
```

- `GET /authorize`
Authorizes a user and saves the token to db

- `GET /oauth2callback`
Used as callback endpoint for google auth servers

