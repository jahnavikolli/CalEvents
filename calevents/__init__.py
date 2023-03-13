from flask import Flask
from flask_sqlalchemy import SQLAlchemy

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.secret_key = '8f42a73054b1749f8f58848be5e6502c'

db = SQLAlchemy(app)

from calevents.models import Tokens

with app.app_context():
    db.create_all()

from calevents import routes
