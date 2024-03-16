from spotify_client import SpotifyClient
from neo4j_client import Neo4jClient, clear_db_artists, clear_db_tracks
from file_utilities import (
    read_genres,
    write_name_id,
    write_to_file,
    read_ids,
    clear_files,
)
import logging

logger = logging.getLogger()


class SixDegrees:
    """Class to handle functionality between Neo4j and Spotify APIs"""

    def __init__(self: "SixDegrees") -> None:
        self._spotify = SpotifyClient()
        self._genres = read_genres("data/genres.txt")
        self._artists = []
        self._artist_ids = set()
        self._tracks = []
        self._track_ids = set()

    def verify_conn(self: "SixDegrees") -> None:
        """Verifies connection to Neo4j database

        Args:
            self (SixDegrees): Instance of SixDegrees
        """
        with Neo4jClient() as neo4j_client:
            neo4j_client.verify_conn()

    def scrape_artists(self: "SixDegrees") -> None:
        """Scrapes the top 250 artists for each genre

        Args:
            self (SixDegrees): Instance of SixDegrees
        """
        limit = 50
        for genre in self._genres:
            offset = 0
            for _ in range(5):
                query = f"genre:{str(genre)}"
                results = self._spotify.search(
                    q=query, cat="artist", limit=limit, offset=offset
                )
                self._artists += results["artists"]["items"]
                if results["artists"]["next"]:
                    offset += limit
                else:
                    break

    def filter_artists(self: "SixDegrees") -> None:
        """Filters artists based on popularity and uniqueness

        Args:
            self (SixDegrees): Instance of SixDegrees
        """
        final_artists = []
        for artist in self._artists:
            artist_id = artist["id"]
            if (
                artist["id"] not in self._artist_ids
                and artist["popularity"] >= 40
            ):
                final_artists.append(artist)
                self._artist_ids.add(artist_id)
                write_name_id("data/artists/artists.txt", artist)
                write_to_file("data/artists/artist_ids.txt", artist_id)
        self._artists = final_artists

    def create_artists(self: "SixDegrees") -> None:
        """Creates artist nodes in Neo4j database

        Args:
            self (SixDegrees): Instance of SixDegrees
        """
        clear_db_artists()
        with Neo4jClient() as neo4j_client:
            for artist in self._artists:
                neo4j_client.create_artist_node(artist)

    def initialize_artists(self: "SixDegrees") -> None:
        """Initializes the artists data using Spotify API

        Args:
            self (SixDegrees): Instance of SixDegrees
        """
        clear_files("data/artists")
        self.scrape_artists()
        self.filter_artists()
        self.create_artists()

    def import_artist_ids(self: "SixDegrees") -> None:
        """Imports artist ids from file

        Args:
            self (SixDegrees): Instance of SixDegrees
        """
        self._artist_ids = read_ids("data/artists/artist_ids.txt")

    def import_artists(self: "SixDegrees") -> None:
        """Imports artists from the id file

        Args:
            self (SixDegrees): Instance of SixDegrees
        """
        self.import_artist_ids()
        id_list = list(self._artist_ids)
        num_ids = len(id_list)
        for i in range(0, num_ids, 50):
            chunk = id_list[i : i + 50] if i + 50 <= num_ids else id_list[i:]
            results = self._spotify.artists(chunk)
            self._artists.extend(results["artists"])
        self.create_artists()

    def scrape_albums(self: "SixDegrees", artist_id: str) -> list:
        """Scrapes albums and singles for a given artist

        Args:
            self (SixDegrees): Instance of SixDegrees
            artist_id (str): Spotify artist id

        Returns:
            list: List of albums and singles
        """
        discography = []
        offset = 0
        limit = 50
        while True:
            logger.info("Scraping albums")
            albums = self._spotify.artist_albums(
                artist_id=artist_id,
                album_type="album,single",
                limit=limit,
                offset=offset,
            )
            discography += albums["items"]
            if albums["next"]:
                offset += limit
            else:
                break
        return discography

    def scrape_tracks(self: "SixDegrees", albums: list) -> list:
        """Scrapes tracks for a given list of albums

        Args:
            self (SixDegrees): Instance of SixDegrees
            albums (list): List of albums

        Returns:
            list: List of tracks
        """
        tracks = []
        for album in albums:
            album_id = album["id"]
            tracks += self._spotify.album_tracks(album_id)["items"]
        return tracks

    def filter_tracks(self: "SixDegrees") -> None:
        """Filters tracks based on artist collaborations. Only one
        collaboration per artist pair is allowed

        Args:
            self (SixDegrees): Instance of SixDegrees
        """
        collabs = set()
        filtered_tracks = []
        for i, track in enumerate(self._tracks):
            logger.info("Filtering tracks %s/%s", i + 1, len(self._tracks))
            track_id = track["id"]
            included_artists = [
                artist
                for artist in track["artists"]
                if artist["id"] in self._artist_ids
            ]
            if len(included_artists) == 0 or len(included_artists) == 1:
                continue
            track_conns = set()
            for i, artist_i in enumerate(included_artists):
                for artist_j in included_artists[i + 1 :]:
                    conn = tuple(sorted([artist_i["id"], artist_j["id"]]))
                    track_conns.add(conn)
            if (
                len(track_conns.intersection(collabs)) == 0
                and track_id not in self._track_ids
            ):
                collabs.update(track_conns)
                filtered_tracks.append(track)
                self._track_ids.add(track["id"])
                write_name_id("data/tracks/tracks.txt", track)
                write_to_file("data/tracks/track_ids.txt", track_id)
        self._tracks = filtered_tracks

    def create_tracks(self: "SixDegrees") -> None:
        """Creates track nodes in Neo4j database

        Args:
            self (SixDegrees): Instance of SixDegrees
        """
        clear_db_tracks()
        with Neo4jClient() as neo4j_client:
            for track in self._tracks:
                neo4j_client.create_track_node(track)

    def initialize_tracks(self: "SixDegrees") -> None:
        """Initializes the tracks data using Spotify API

        Args:
            self (SixDegrees): Instance of SixDegrees
        """
        clear_files("data/tracks")
        self.import_artist_ids()
        for i, artist_id in enumerate(self._artist_ids):
            logger.info(
                "Scraping albums for artist %s/%s", i + 1, len(self._artist_ids)
            )
            albums = self.scrape_albums(artist_id)
            logger.info(
                "Scraping tracks for artist %s/%s", i + 1, len(self._artist_ids)
            )
            self._tracks += self.scrape_tracks(albums)
        self.filter_tracks()
        self.create_tracks()

    def import_track_ids(self: "SixDegrees") -> None:
        """Imports track ids from file

        Args:
            self (SixDegrees): Instance of SixDegrees
        """
        self._track_ids = read_ids("data/tracks/track_ids.txt")

    def import_tracks(self: "SixDegrees") -> None:
        """Imports tracks from the id file

        Args:
            self (SixDegrees): Instance of SixDegrees
        """
        self.import_track_ids()
        id_list = list(self._track_ids)
        num_ids = len(id_list)
        for i in range(0, num_ids, 50):
            chunk = id_list[i : i + 50] if i + 50 <= num_ids else id_list[i:]
            results = self._spotify.tracks(chunk)
            self._tracks.extend(results["tracks"])
        self.create_tracks()

    def create_relationships(self: "SixDegrees") -> None:
        """Creates relationships between artists and tracks in Neo4j database

        Args:
            self (SixDegrees): Instance of SixDegrees
        """
        with Neo4jClient() as neo4j_manager:
            neo4j_manager.create_relationships()

    def initialize_data(self: "SixDegrees") -> None:
        """Initializes the artists, tracks, and relationships in the Neo4j
        database with Spotify API

        Args:
            self (SixDegrees): Instance of SixDegrees
        """
        self.initialize_artists()
        self.initialize_tracks()
        self.create_relationships()

    def import_data(self: "SixDegrees") -> None:
        """Imports the artists, tracks, and relationships in the Neo4j
        database with given files

        Args:
            self (SixDegrees): Instance of SixDegrees
        """
        self.import_artists()
        self.import_tracks()
        self.create_relationships()
