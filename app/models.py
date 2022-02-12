from datetime import datetime
from app import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), index=True)
    lastname = db.Column(db.String(160), index=True)
    email = db.Column(db.String(160), index=True, unique=True)
    password_hash = db.Column(db.String(160))
    posts = db.relationship('Contest', backref='User', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.email)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Contest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160))
    banner = db.Column(db.String(160))
    url = db.Column(db.String(160))
    startDate = db.Column(db.DateTime, index=True)
    endDate = db.Column(db.DateTime, index=True)
    payment = db.Column(db.Integer)
    script = db.Column(db.String(160))
    address = db.Column(db.String(160))
    notes = db.Column(db.String(160))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post {}>'.format(self.body)


class Form(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(160), index=True)
    name = db.Column(db.String(160))
    lastname = db.Column(db.String(160), index=True)
    uploadDate = db.Column(db.DateTime, index=True)
    state = db.Column(db.String(160)) ##
    original = db.Column(db.String(160)) ##RUTA DEL ARCHIVO
    formatted = db.Column(db.String(160)) ##BLANK
    notes = db.Column(db.String(160)) 
    contest_id = db.Column(db.Integer, db.ForeignKey('contest.id'))