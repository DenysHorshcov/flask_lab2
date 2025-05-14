from flask import Blueprint, request, render_template

from .models import db
from sqlalchemy.sql import text
from .models import Movie, MoviePerson, Person, PersonRole, Role
from .tmdb_loader import fetch_and_store_popular_movies
from flask import jsonify
import json

main = Blueprint('main', __name__)

@main.route('/')
def index():
    movies = Movie.query.order_by(Movie.popularity.desc()).all()
    movies_json = json.dumps([
        {
            "id": movie.id,
            "title": movie.title,
            "release": movie.release.strftime('%Y-%m-%d') if movie.release else "",
            "imdb_score": movie.imdb_score or "",
            "popularity": movie.popularity or 0
        }
        for movie in movies
    ])
    return render_template('index.html', movies_json=movies_json)


@main.route('/movies/load')
def load_more_movies():
    page = request.args.get('page', 1, type=int)
    per_page = 5
    movies = Movie.query.order_by(Movie.popularity.desc()).paginate(page=page, per_page=per_page)
    movies_data = [{
        'title': movie.title,
        'release': movie.release.strftime('%Y-%m-%d') if movie.release else "Unknown",
        'imdb_score': movie.imdb_score
    } for movie in movies.items]
    return {'movies': movies_data, 'has_next': movies.has_next}

@main.route('/movie/<int:movie_id>')
def movie_detail(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    
    # знайти усіх людей, які брали участь у фільмі
    movie_persons = db.session.query(Person, Role).\
        join(MoviePerson, MoviePerson.person_id == Person.id).\
        join(PersonRole, PersonRole.person_id == Person.id).\
        join(Role, Role.id == PersonRole.role_id).\
        filter(MoviePerson.movie_id == movie_id).all()

    # групуємо по ролях
    cast_by_role = {}
    for person, role in movie_persons:
        if role.title not in cast_by_role:
            cast_by_role[role.title] = []
        cast_by_role[role.title].append(person)

    return render_template('movie_detail.html', movie=movie, cast_by_role=cast_by_role)

@main.route('/person/<int:person_id>')
def person_detail(person_id):
    person = Person.query.get_or_404(person_id)

    # знайти усі ролі людини і в яких фільмах
    roles_movies = db.session.query(Role.title, Movie.title, Movie.id).\
        join(PersonRole, PersonRole.role_id == Role.id).\
        join(MoviePerson, MoviePerson.person_id == PersonRole.person_id).\
        join(Movie, Movie.id == MoviePerson.movie_id).\
        filter(PersonRole.person_id == person_id).all()

    # групуємо за ролями
    roles_data = {}
    for role_title, movie_title, movie_id in roles_movies:
        if role_title not in roles_data:
            roles_data[role_title] = []
        roles_data[role_title].append({'movie_title': movie_title, 'movie_id': movie_id})

    return render_template('person_detail.html', person=person, roles_data=roles_data)


@main.route("/load-tmdb")
def load_tmdb():
    print("🔵 /load-tmdb route called")
    try:
        fetch_and_store_popular_movies()
        return "✅ TMDb loaded"
    except Exception as e:
        print(f"❌ ERROR during TMDb fetch: {e}")
        return f"❌ Error: {e}", 500
