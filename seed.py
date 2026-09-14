from app import app
from models import db, Venue, Artist, Show, Genre
from seed_data import SHOWS, VENUES, ARTISTS, GENRES
from sqlalchemy import text

def seed():
    with app.app_context():
        try:
            # Seed genres
            for genre in GENRES:
                if db.session.get(Genre, genre["id"]) is None:
                    db.session.add(Genre(**genre))
            db.session.flush()

            # Seed venues
            for venue in VENUES:
                if db.session.get(Venue, venue["id"]) is None:

                    genre_ids = [int(gid) for gid in venue.get("genres", [])]

                    if genre_ids:
                        # 2. Fetch all matching genres in a single SQL query
                        genres = db.session.scalars(
                            db.select(Genre).filter(Genre.id.in_(genre_ids))
                        ).all()

                        # 3. Validation: Ensure every requested ID was found in the database
                        if len(genres) != len(set(genre_ids)):
                            missing = set(genre_ids) - {g.id for g in genres}
                            raise ValueError(f"Genres with IDs {missing} do not exist.")
                    else:
                        genres = []

                    venue["genres"] = genres
                    db.session.add(Venue(**venue))

            # Seed artists
            for artist in ARTISTS:
                if db.session.get(Artist, artist["id"]) is None:

                    genre_ids = [int(gid) for gid in artist.get("genres", [])]

                    if genre_ids:
                        # 2. Fetch all matching genres in a single SQL query
                        genres = db.session.scalars(
                            db.select(Genre).filter(Genre.id.in_(genre_ids))
                        ).all()

                        # 3. Validation: Ensure every requested ID was found in the database
                        if len(genres) != len(set(genre_ids)):
                            missing = set(genre_ids) - {g.id for g in genres}
                            raise ValueError(f"Genres with IDs {missing} do not exist.")
                    else:
                        genres = []

                    artist["genres"] = genres
                    db.session.add(Artist(**artist))

            

            # Seed shows
            for show in SHOWS:
                show_data = show.copy()
                if db.session.get(Show, show_data["id"]) is None:
                    db.session.add(Show(**show_data))


            # Send all pending inserts to the database before checking MAX(id).
            db.session.flush()

            # Synchronize automatic IDs with the explicitly seeded IDs.
            for table_name in ("venue", "artist", "genre", "show"):
                db.session.execute(text(f"""
                    SELECT setval(
                        pg_get_serial_sequence('{table_name}', 'id'),
                        COALESCE(MAX(id), 1),
                        MAX(id) IS NOT NULL
                    )
                    FROM {table_name}
                """))

            db.session.commit()
            print(f"Seeding completed.")

        except Exception:
            db.session.rollback()
            raise


if __name__ == "__main__":
    seed()
