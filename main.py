import os

from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.fields.numeric import IntegerField
from wtforms.fields.simple import TextAreaField, HiddenField
from wtforms.validators import DataRequired
import requests

API_URL = 'https://api.themoviedb.org/3/search/movie'
MOVIE_INFO_URL = 'https://api.themoviedb.org/3/movie'
MOVIE_IMAGE_URL = "https://image.tmdb.org/t/p/w500"
API_KEY = '353a5b4bd5e61f2b9f4ac47e3fa5ef86'
API_TOKEN = os.environ.get('API_TOKEN')

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movies-collection.db"
Bootstrap5(app)
db = SQLAlchemy(app)


class Movie(db.Model):
    id = db.Column('book_id', db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, unique=True)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.Text, nullable=True)
    img_url = db.Column(db.String(250), nullable=False)

    # def __init__(self, title, year, description, rating, ranking, review, img_url):
    #     self.title = title
    #     self.year = year
    #     self.description = description
    #     self.rating = rating
    #     self.ranking = ranking
    #     self.review = review
    #     self.img_url = img_url


with app.app_context():
    db.create_all()


class EditMovieForm(FlaskForm):
    id = HiddenField("Movie ID")
    rating = IntegerField('Rating (from 1 to 10)', validators=[DataRequired()])
    review = TextAreaField('Your review', validators=[DataRequired()])
    submit = SubmitField('Done')


class AddMovieForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')


@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating.desc()))
    all_movies = result.scalars().all()
    print(all_movies[0].title)
    rank = 1
    for movie in all_movies:
        movie.ranking = rank
        rank += 1
    db.session.commit()
    print(all_movies[0].title)
    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=["GET", "POST"])
def edit_movie():
    movie_id = request.args.get('id')
    movie_selected = Movie.query.get_or_404(movie_id)
    form = EditMovieForm(id=movie_id)
    if form.validate_on_submit():
        movie_to_update = Movie.query.get_or_404(form.id.data)
        movie_to_update.rating = form.rating.data
        movie_to_update.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", form=form, movie=movie_selected)


@app.route("/delete", methods=["GET", "POST"])
def delete_movie():
    movie_id = request.args.get('id')
    Movie.query.filter_by(id=movie_id).delete()
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=["GET", "POST"])
def add_movie():
    form = AddMovieForm()
    if form.validate_on_submit():
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {API_TOKEN}",
        }
        params = {
            "query": form.title.data,
            "include_adult": True,
        }
        response = requests.get(API_URL, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()['results']
        return render_template('select.html', movies=data)
    return render_template("add.html", form=form)


@app.route("/find")
def find_movie():
    movie_api_id = request.args.get("id")
    if movie_api_id:
        movie_api_url = f"{MOVIE_INFO_URL}/{movie_api_id}"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {API_TOKEN}",
        }
        response = requests.get(movie_api_url, headers=headers, params={"language": "en-US"})
        data = response.json()
        new_movie = Movie(
            title=data["title"],
            year=data["release_date"].split("-")[0],
            img_url=f"{MOVIE_IMAGE_URL}{data['poster_path']}",
            description=data["overview"],
        )
        db.session.add(new_movie)
        db.session.commit()

        # Redirect to /edit route
        return redirect(url_for("edit_movie", id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
