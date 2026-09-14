from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#

venue_genres = db.Table(
    "venue_genres",
    db.Column("venue_id", db.Integer, db.ForeignKey("venue.id"), primary_key=True),
    db.Column("genre_id", db.Integer, db.ForeignKey("genre.id"), primary_key=True),
)

artist_genres = db.Table(
    "artist_genres",
    db.Column("artist_id", db.Integer, db.ForeignKey("artist.id"), primary_key=True),
    db.Column("genre_id", db.Integer, db.ForeignKey("genre.id"), primary_key=True),
)


class Genre(db.Model):
    __tablename__ = "genre"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    venues = db.relationship("Venue", secondary=venue_genres, back_populates="genres")
    artists = db.relationship(
        "Artist", secondary=artist_genres, back_populates="genres"
    )


class Venue(db.Model):
    __tablename__ = "venue"

    __table_args__ = (
        db.UniqueConstraint("name", "city", "state", name="uq_venue_name_city_state"),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    website_link = db.Column(db.String(500))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.relationship("Genre", secondary=venue_genres, back_populates="venues")
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship("Show", back_populates="venue")


class Artist(db.Model):
    __tablename__ = "artist"

    __table_args__ = (
        db.UniqueConstraint(
            "name", "state", "website_link", name="uq_artist_name_state_website"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    genres = db.relationship("Genre", secondary=artist_genres, back_populates="artists")
    website_link = db.Column(db.String(500))
    seeking_description = db.Column(db.String(500))
    seeking_venue = db.Column(db.Boolean, default=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    shows = db.relationship("Show", back_populates="artist")


class Show(db.Model):
    __tablename__ = "show"

    __table_args__ = (
        db.UniqueConstraint(
            "artist_id",
            "venue_id",
            "start_time",
            name="uq_show_artist_venue_start_time",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey("venue.id"), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey("artist.id"), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)

    venue = db.relationship("Venue", back_populates="shows")
    artist = db.relationship("Artist", back_populates="shows")
