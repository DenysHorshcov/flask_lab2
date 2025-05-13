from flask import Blueprint, request, render_template

from .models import db
from sqlalchemy.sql import text
from .models import Movie, MoviePerson, Person, PersonRole, Role
from .tmdb_loader import fetch_and_store_popular_movies

main = Blueprint('main', __name__)

@main.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 5

    movies = Movie.query.order_by(Movie.popularity.desc()).paginate(page=page, per_page=per_page)
    return render_template('index.html', movies=movies)

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


@main.route("/load-tmdb")
def load_tmdb():
    print("🔵 /load-tmdb route called")
    try:
        fetch_and_store_popular_movies()
        return "✅ TMDb loaded"
    except Exception as e:
        print(f"❌ ERROR during TMDb fetch: {e}")
        return f"❌ Error: {e}", 500
