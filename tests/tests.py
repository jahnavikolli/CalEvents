import urllib
from flask import Flask
from flask_testing import TestCase
from calevents import app, db
from calevents.models import Tokens

class Tests(TestCase):
    SQLALCHEMY_DATABASE_URI = "sqlite://test"
    TESTING = True

    def create_app(self):
        app.config['TESTING'] = True
        return app
    
    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_server_is_up_and_running(self):
        response = self.client.get("/")
        self.assertEqual(response.code, 200)
    
    def test_bad_request(self):
        # timemin or timemax not provided
        req_url = "/listEvents?userid=userid"
        
        response = self.client.get(req_url)
        self.assertEqual(response.code, 400)
    
    def test_valid_token(self):
        # Add a valid test token(skipping the auth flow)
        token = Tokens("testUser", "<TEST TOKEN>")
        db.session.add(token)
        db.session.commit()

        req_url = "/listEvents?userid=testUser&timemin=<TIME>&timemax=<TIME>"
        response = self.client.get(req_url)
        self.assertEqual(response.code, 200)

    def test_expired_token(self):
        # Add a valid test token(skipping the auth flow)
        token = Tokens("testUser", "<EXPIRED TEST TOKEN>")
        db.session.add(token)
        db.session.commit()

        req_url = "/listEvents?userid=testUser&timemin=<TIME>&timemax=<TIME>"
        response = self.client.get(req_url)
        self.assertEqual(response.code, 200)

    def test_table_structure(self):
        self.assertRaises(BaseException, Tokens("testUser", None))


