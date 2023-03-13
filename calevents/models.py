from calevents import db

class Tokens(db.Model):
    userid = db.Column(db.String(100), primary_key=True)
    token = db.Column(db.String(300), nullable=False)

    def __repr__(self):
        return self.userid + ": " + self.token 