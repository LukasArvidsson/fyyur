# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import dateutil.parser
import babel
from flask import Flask, abort, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from forms import *
from models import db, Venue, Artist, Show, Genre

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)

# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():

    venue_records = db.session.scalars(
        db.select(Venue).order_by(Venue.city, Venue.state, Venue.name)).all()

    areas = {}

    for venue in venue_records:
        key = (venue.city, venue.state)

        if key not in areas:
            areas[key] = {
                "city": venue.city,
                "state": venue.state,
                "venues": [],
            }

        areas[key]["venues"].append({
            "id": venue.id,
            "name": venue.name,
            "image_link": venue.image_link,
        })
     
    return render_template("pages/venues.html", areas=list(areas.values()))

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term', '').strip()

  venue_records = []

  if search_term:
        venue_records = db.session.scalars(
            db.select(Venue)
            .where(Venue.name.icontains(search_term, autoescape=True))
            .order_by(Venue.name)
        ).all()

  now = datetime.now()

  response = {
    "data": [
        {
          "id": venue.id,
          "name": venue.name,
          "image_link": venue.image_link,
          "num_upcoming_shows": sum(
              show.start_time >= now
              for show in venue.shows
          ),
        }
        for venue in venue_records
    ],
    "count": len(venue_records),
  }

  return render_template(
    'pages/search_venues.html',
    results=response,
    search_term=search_term
  )

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

  venue = db.session.get(Venue, venue_id)
  if venue is None :
      abort(404)

  now = datetime.now()

  past_shows = []
  upcoming_shows = []

  for show in sorted(venue.shows, key=lambda show: show.start_time):
    show_data = {
        "artist_id": show.artist_id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": show.start_time.isoformat(),
    }

    if show.start_time < now:
        past_shows.append(show_data)
    else:
        upcoming_shows.append(show_data)

  data = {
      "id": venue.id,
      "name": venue.name,
      "genres": [genre.name for genre in venue.genres],
      "address": venue.address,
      "city": venue.city,
      "state": venue.state,
      "phone": venue.phone,
      "website_link": venue.website_link,
      "facebook_link": venue.facebook_link,
      "image_link": venue.image_link,
      "seeking_talent": venue.seeking_talent,
      "seeking_description": venue.seeking_description,
      "past_shows": past_shows,
      "upcoming_shows": upcoming_shows,
      "past_shows_count": len(past_shows),
      "upcoming_shows_count": len(upcoming_shows),
  }

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()

    genres = db.session.scalars(db.select(Genre).order_by(Genre.name)).all()

    set_genre_choices(form, genres)
    return render_template("forms/new_venue.html", form=form)


@app.route("/venues/create", methods=["POST"])
def create_venue_submission():

  form = VenueForm(formdata=request.form)

  genres = db.session.scalars(db.select(Genre).order_by(Genre.name)).all()
  set_genre_choices(form, genres)

  if not form.validate():
    flash('Please correct the errors below.')
    return render_template('forms/new_venue.html', form=form), 400

  selected_ids = set(form.genres.data)

  venue = Venue(
    name=form.name.data,
    city=form.city.data,
    state=form.state.data,
    address=form.address.data,
    phone=form.phone.data,
    image_link=form.image_link.data,
    facebook_link=form.facebook_link.data,
    website_link=form.website_link.data,
    seeking_talent=form.seeking_talent.data,
    seeking_description=form.seeking_description.data,
    genres=[g for g in genres if g.id in selected_ids],
  )

  try:
    db.session.add(venue)
    db.session.commit()

  except Exception:
    db.session.rollback()
    app.logger.exception("Failed to create venue")
    flash('The venue could not be saved. Please try again.')
    return render_template('forms/new_venue.html', form=form), 500

  finally:
    db.session.close()

  flash('Venue ' + form.name.data + ' was successfully listed!')
  return redirect(url_for('index'))


@app.route('/venues/<int:venue_id>/delete', methods=['POST'])
def delete_venue(venue_id):

  venue = db.session.get(Venue, venue_id)

  if venue is None:
    abort(404)

  if venue.shows:
    flash('The venue could not be deleted since it has associated shows.')
    return redirect(
        url_for('show_venue', venue_id=venue_id),
        code=303,
    )

  try:
    db.session.delete(venue)
    db.session.commit()
    flash('The venue was successfully deleted.')
    return redirect(url_for('venues'), code=303)
  
  except Exception:
    db.session.rollback()
    app.logger.exception("Failed to delete venue")
    flash('The venue could not be deleted. Please try again.')
    return redirect(url_for('venues'), code=303)


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():

  artist_records = db.session.scalars(
      db.select(Artist).order_by(Artist.name)
  ).all()

  return render_template('pages/artists.html', artists=artist_records)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  artist_records = []
  
  search_term = request.form.get('search_term', '').strip()
  
  if search_term:
        artist_records = db.session.scalars(
            db.select(Artist)
            .where(Artist.name.icontains(search_term, autoescape=True))
            .order_by(Artist.name)
        ).all()
  
  now = datetime.now()

  response = {
    "data": [
        {
          "id": artist.id,
          "name": artist.name,
          "image_link": artist.image_link,
          "num_upcoming_shows": sum(
              show.start_time >= now
              for show in artist.shows
          ),
        }
        for artist in artist_records
    ],
    "count": len(artist_records),
  }

  return render_template(
    'pages/search_artists.html',
    results=response,
    search_term=search_term
  )

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  artist = db.session.get(Artist, artist_id)

  if artist is None:
    abort(404)

  now = datetime.now()

  past_shows = []
  upcoming_shows = []
  for show in artist.shows:
    if show.start_time < now:
      past_shows.append({
        "venue_id": show.venue.id,
        "venue_name": show.venue.name,
        "venue_image_link": show.venue.image_link,
        "start_time": show.start_time.isoformat()
      })
    else:
      upcoming_shows.append({
        "venue_id": show.venue.id,
        "venue_name": show.venue.name,
        "venue_image_link": show.venue.image_link,
        "start_time": show.start_time.isoformat()
      })

  data = {
    "id": artist.id,
    "name": artist.name,
    "genres": [genre.name for genre in artist.genres],
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website_link": artist.website_link,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
  }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):

  artist = db.session.get(Artist, artist_id)

  if artist is None:
    abort(404)

  form = ArtistForm(obj=artist)

  genres = db.session.scalars(db.select(Genre).order_by(Genre.name)).all()
  set_genre_choices(form, genres)

  form.genres.data = [genre.id for genre in artist.genres]

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  artist = db.session.get(Artist, artist_id)

  form = ArtistForm(formdata=request.form)

  if artist is None:
     abort(404)

  genres = db.session.scalars(db.select(Genre).order_by(Genre.name)).all()
  set_genre_choices(form, genres)

  if not form.validate():
    flash('Please correct the errors below.')
    return render_template('forms/edit_artist.html', form=form, artist=artist), 400

  try:
    artist.name = form.name.data
    artist.city = form.city.data
    artist.state = form.state.data
    artist.phone = form.phone.data
    artist.website_link = form.website_link.data
    artist.facebook_link = form.facebook_link.data
    artist.seeking_venue = form.seeking_venue.data
    artist.seeking_description = form.seeking_description.data
    artist.image_link = form.image_link.data
    artist.genres = [g for g in genres if g.id in form.genres.data]
    db.session.commit()

  except Exception:
    db.session.rollback()
    app.logger.exception("Failed to update artist")
    flash('The artist could not be updated. Please try again.')
    return render_template('forms/edit_artist.html', form=form, artist=artist), 500

  finally:
    db.session.close()

  flash('The artist was successfully updated.')
  return redirect(url_for('show_artist', artist_id=artist_id), code=303)

@app.route('/artists/<int:artist_id>/delete', methods=['POST'])
def delete_artist(artist_id):

  artist = db.session.get(Artist, artist_id)

  if artist is None:
    abort(404)

  if artist.shows:
    flash('The artist could not be deleted since it has associated shows.')
    return redirect(
      url_for('show_artist', artist_id=artist_id),
      code=303,
    )

  try:
    db.session.delete(artist)
    db.session.commit()
    flash('The artist was successfully deleted.')
    return redirect(url_for('artists'), code=303)
  
  except Exception:
    db.session.rollback()
    app.logger.exception("Failed to delete artist")
    flash('The artist could not be deleted. Please try again.')
    return redirect(url_for('artists'), code=303)

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):

  venue = db.session.get(Venue, venue_id)

  if venue is None:
    abort(404)

  # Populate fields with values from the venue object
  form = VenueForm(obj=venue)

  genres = db.session.scalars(db.select(Genre).order_by(Genre.name)).all()
  set_genre_choices(form, genres)

  form.genres.data = [genre.id for genre in venue.genres]

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

  venue = db.session.get(Venue, venue_id)

  if venue is None:
    abort(404)

  form = VenueForm(formdata=request.form)

  genres = db.session.scalars(db.select(Genre).order_by(Genre.name)).all()
  set_genre_choices(form, genres)

  if not form.validate():
    flash('Please correct the errors below.')
    return render_template('forms/edit_venue.html', form=form, venue=venue), 400

  try:
    venue.name = form.name.data
    venue.city = form.city.data
    venue.state = form.state.data
    venue.address = form.address.data
    venue.phone = form.phone.data
    venue.image_link = form.image_link.data
    venue.facebook_link = form.facebook_link.data
    venue.website_link = form.website_link.data
    venue.seeking_talent = form.seeking_talent.data
    venue.seeking_description = form.seeking_description.data
    venue.genres = [g for g in genres if g.id in form.genres.data]
    db.session.commit()

  except Exception:
    db.session.rollback()
    app.logger.exception("Failed to update venue")
    flash('The venue could not be updated. Please try again.')
    return render_template('forms/edit_venue.html', form=form, venue=venue), 500

  finally:
    db.session.close()

  flash('Venue ' + form.name.data + ' was successfully updated!')
  return redirect(url_for('show_venue', venue_id=venue_id),code=303)

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  
  genres = db.session.scalars(db.select(Genre).order_by(Genre.name)).all()
  
  set_genre_choices(form, genres)
  return render_template("forms/new_artist.html", form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():

  form = ArtistForm(formdata=request.form)
  
  genres = db.session.scalars(db.select(Genre).order_by(Genre.name)).all()
  set_genre_choices(form, genres)

  if not form.validate():
    flash('Please correct the errors below.')
    return render_template('forms/new_artist.html', form=form), 400

  selected_ids = set(form.genres.data)

  artist = Artist(
    name=form.name.data,
    city=form.city.data,
    state=form.state.data,
    phone=form.phone.data,
    image_link=form.image_link.data,
    facebook_link=form.facebook_link.data,
    website_link=form.website_link.data,
    seeking_venue=form.seeking_venue.data,
    seeking_description=form.seeking_description.data,
    genres=[g for g in genres if g.id in selected_ids],
  )

  try:
    db.session.add(artist)
    db.session.commit()

  except Exception:
    db.session.rollback()
    app.logger.exception("Failed to create artist")
    flash('The artist could not be saved. Please try again.')
    return render_template('forms/new_artist.html', form=form), 500

  finally:
    db.session.close()

  flash('Artist ' + form.name.data + ' was successfully listed!')
  return redirect(url_for('index'))

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  show_records = db.session.scalars(db.select(Show).order_by(Show.start_time)).all()

  data = []
  for show in show_records:
    data.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.isoformat()
    })

  print(show_records)

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():

  form = ShowForm(formdata=request.form)
  
  if not form.validate():
    flash('Please correct the errors below.')
    return render_template('forms/new_show.html', form=form), 400

  if db.session.get(Artist, form.artist_id.data) is None:
    form.artist_id.errors.append('Artist not found.')

  if db.session.get(Venue, form.venue_id.data) is None:
    form.venue_id.errors.append('Venue not found.')

  if form.errors:
    return render_template('forms/new_show.html', form=form), 400
  
  show = Show(
    venue_id=form.venue_id.data,
    artist_id=form.artist_id.data,
    start_time=form.start_time.data,
  )

  try:
    db.session.add(show)
    db.session.commit()

  except Exception:
    db.session.rollback()
    app.logger.exception("Failed to create show")
    flash('The show could not be saved. Please try again.')
    return render_template('forms/new_show.html', form=form), 500

  finally:
    db.session.close()

  flash('Show was successfully listed!')
  return redirect(url_for('index'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
