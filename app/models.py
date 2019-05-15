from app import app, db, login
from datetime import datetime
from time import time
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5
import jwt

@login.user_loader
def load_user(id):
    return User.query.get(int(id))


followers = db.Table(
    'followers',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('event_id', db.Integer, db.ForeignKey('event.id'))
    )


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    last_name = db.Column(db.String(100))
    first_name = db.Column(db.String(50))
    date = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    sum_b = db.Column(db.Integer)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=mp&s={}'.format(
            digest, size)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def follow(self, event_id):
        if not self.is_following(event_id):
            self.followed_events.append(Event.query.get(event_id))

    def unfollow(self, event_id):
        if self.is_following(event_id):
            self.followed_events.remove(Event.query.get(event_id))

    def is_following(self, event_id):
        return self.followed_events.filter(
            followers.c.event_id == event_id).count() > 0

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    place = db.Column(db.String(100))
    date_event = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    b_count = db.Column(db.Integer)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'))
    followers = db.relationship(
        'User', secondary=followers,
        backref=db.backref('followed_events', lazy='dynamic'), lazy='dynamic')


    def __repr__(self):
        return '<Event {}>'.format(self.name)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.event_id == user.id).count() > 0


class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login_name = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    email = db.Column(db.String(120), index=True, unique=True)
    name = db.Column(db.String(100), index=True)
    address = db.Column(db.String(100))
    events = db.relationship('Event', backref='sponsor', lazy='dynamic')

    def __repr__(self):
        return '<Company {}>'.format(self.login_name)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return Company.query.get(id)