import requests
from datetime import datetime
from flask import current_app
from .models import db, Movie, Person, Role, MoviePerson, PersonRole
from sqlalchemy import exists

def fetch_and_store_popular_movies():
    api_key = current_app.config["TMDB_API_KEY"]
    base_url = "https://api.themoviedb.org/3"

    popular_url = f"{base_url}/movie/popular?api_key={api_key}&language=en-US&page=1"
    movies = requests.get(popular_url).json().get("results", [])

    for movie_data in movies:
        if not movie_data.get("title"):
            continue

        # Avoid duplicate movie
        if db.session.query(exists().where(Movie.title == movie_data["title"])).scalar():
            continue

        movie = Movie(
            title=movie_data["title"],
            release=datetime.strptime(movie_data["release_date"], "%Y-%m-%d") if movie_data.get("release_date") else None,
            imdb_score=movie_data.get("vote_average", 0),
            popularity=movie_data.get("popularity", 0)
        )
        db.session.add(movie)
        db.session.flush()  # to access movie.id

        # Fetch credits
        movie_id = movie_data["id"]
        credits_url = f"{base_url}/movie/{movie_id}/credits?api_key={api_key}"
        credits = requests.get(credits_url).json()

        # --- Cast → Actor Role ---
        for person_data in credits.get("cast", [])[:10]:  # limit to top 10
            add_person_with_role(person_data, "Actor", movie)

        # --- Crew → actual roles from TMDb ---
        for person_data in credits.get("crew", []):
            job = person_data.get("job")
            if job:
                add_person_with_role(person_data, job, movie)

    db.session.commit()

def add_person_with_role(person_data, role_title, movie):
    name = person_data.get("name")
    if not name:
        return

    # Get or create Person
    person = Person.query.filter_by(name=name).first()
    if not person:
        person = Person(name=name, birthday=datetime(1900, 1, 1))
        db.session.add(person)
        db.session.flush()

    # Get or create Role
    role = Role.query.filter_by(title=role_title).first()
    if not role:
        role = Role(title=role_title)
        db.session.add(role)
        db.session.flush()

    # Link MoviePerson (many-to-many)
    if not MoviePerson.query.filter_by(movie_id=movie.id, person_id=person.id).first():
        db.session.add(MoviePerson(movie_id=movie.id, person_id=person.id))

    # Link PersonRole (many-to-many)
    if not PersonRole.query.filter_by(person_id=person.id, role_id=role.id).first():
        db.session.add(PersonRole(person_id=person.id, role_id=role.id))
