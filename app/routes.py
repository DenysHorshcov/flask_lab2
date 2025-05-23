from flask import Blueprint, request, render_template

from .models import db
from sqlalchemy.sql import text
from .models import Movie, MoviePerson, Person, PersonRole, Role, UserMovieRating
from .tmdb_loader import fetch_and_store_popular_movies
from flask import jsonify
from flask import flash
from app.models import User
from flask import redirect, url_for
import json

main = Blueprint('main', __name__)

@main.route('/')
def index():
    movies = Movie.query.all()
    movies_json = [
        {
            'id': movie.id,
            'title': movie.title,
            'release': movie.release.strftime('%Y-%m-%d') if movie.release else '',
            'imdb_score': movie.imdb_score,
            'popularity': movie.popularity
        }
        for movie in movies
    ]

    user_ratings = []
    if current_user.is_authenticated:
        user_ratings = [
            {'movie_id': r.movie_id, 'rating': r.rating}
            for r in UserMovieRating.query.filter_by(user_id=current_user.id).all()
        ]

    return render_template(
        'index.html',
        movies_json=movies_json,
        user_ratings=user_ratings,
        is_authenticated=current_user.is_authenticated,
        current_user_id=current_user.get_id() if current_user.is_authenticated else None
    )

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

    # додано: отримати оцінку поточного користувача, якщо є
    user_rating = None
    if current_user.is_authenticated:
        rating = UserMovieRating.query.filter_by(user_id=current_user.id, movie_id=movie.id).first()
        if rating:
            user_rating = rating.rating

    return render_template(
        'movie_detail.html',
        movie=movie,
        cast_by_role=cast_by_role,
        user_rating=user_rating
    )


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

from flask_login import login_required, current_user

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        new_username = request.form.get('new_username')
        if new_username:
            existing_user = User.query.filter_by(username=new_username).first()
            if existing_user:
                flash('This username is already taken. Please choose another.', 'danger')
            else:
                current_user.username = new_username
                db.session.commit()
                flash('Username updated successfully!', 'success')
        return redirect(url_for('main.profile'))
    
    # Якщо метод GET — просто показуємо форму
    return render_template('edit_profile.html')


from flask import request
from app.models import UserMovieRating, Movie

# @main.route('/rate-movie/<int:movie_id>', methods=['POST'])
# @login_required
# def rate_movie(movie_id):
#     rating = request.form.get('rating')

#     if not rating:
#         flash('Rating is required.', 'danger')
#         return redirect(url_for('main.index'))

#     # Перевірити чи є такий фільм
#     movie = Movie.query.get(movie_id)
#     if not movie:
#         flash('Movie not found.', 'danger')
#         return redirect(url_for('main.index'))

#     # Додати оцінку в спеціальну таблицю (наприклад UserMovie)
#     user_movie = UserMovieRating.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
#     if user_movie:
#         user_movie.rating = rating
#     else:
#         user_movie = UserMovieRating(user_id=current_user.id, movie_id=movie_id, rating=rating)
#         db.session.add(user_movie)

#     db.session.commit()
#     flash('Your rating has been saved!', 'success')
#     return redirect(url_for('main.index'))

@main.route('/rate-movie/<int:movie_id>', methods=['POST'])
@login_required
def rate_movie(movie_id):
    data = request.get_json()
    action = data.get('action')
    movie = Movie.query.get_or_404(movie_id)

    existing_rating = UserMovieRating.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()

    if action == 'delete':
        if existing_rating:
            db.session.delete(existing_rating)
            db.session.commit()
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'No rating to delete'}), 404

    rating = data.get('rating')
    if rating is None:
        return jsonify({'error': 'Rating is required'}), 400

    if existing_rating:
        existing_rating.rating = rating
    else:
        new_rating = UserMovieRating(user_id=current_user.id, movie_id=movie_id, rating=rating)
        db.session.add(new_rating)

    db.session.commit()
    return jsonify({'success': True})



@main.route('/edit-rating/<int:movie_id>', methods=['POST'])
@login_required
def edit_rating(movie_id):
    data = request.get_json()
    new_rating = data.get('rating')
    rating = UserMovieRating.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
    if rating:
        rating.rating = new_rating
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False}), 404

@main.route('/delete-rating/<int:movie_id>', methods=['DELETE'])
@login_required
def delete_rating(movie_id):
    rating = UserMovieRating.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
    if rating:
        db.session.delete(rating)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False}), 404
