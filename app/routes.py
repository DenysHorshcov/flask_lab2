from flask import Blueprint, render_template
from .models import db
from sqlalchemy.sql import text
from .models import Movie
from .tmdb_loader import fetch_and_store_popular_movies

main = Blueprint('main', __name__)

@main.route('/')
def index():
    movies = Movie.query.order_by(Movie.popularity.desc()).limit(20).all()
    return render_template('index.html', movies=movies)

@main.route("/load-tmdb")
def load_tmdb():
    print("🔵 /load-tmdb route called")
    try:
        fetch_and_store_popular_movies()
        return "✅ TMDb loaded"
    except Exception as e:
        print(f"❌ ERROR during TMDb fetch: {e}")
        return f"❌ Error: {e}", 500
