from . import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class UserMovieRating(db.Model):
    __tablename__ = 'user_movie_rating'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)
    rating = db.Column(db.Float, nullable=False)

    user = db.relationship('User', backref=db.backref('ratings', lazy=True, cascade='all, delete-orphan'))
    movie = db.relationship('Movie', backref=db.backref('ratings', lazy=True, cascade='all, delete-orphan'))

    __table_args__ = (db.UniqueConstraint('user_id', 'movie_id', name='_user_movie_uc'),)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    release = db.Column(db.Date, nullable=True)
    imdb_score = db.Column(db.Float, nullable=False)
    popularity = db.Column(db.Integer, nullable=False)

class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    birthday = db.Column(db.Date, nullable=True)

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)

class MoviePerson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('movie_id', 'person_id', name='unique_movie_person'),
    )

class PersonRole(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('person_id', 'role_id', name='unique_person_role'),
    )
