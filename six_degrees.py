from spotify_client import SpotifyClient
from neo4j_client import Neo4jClient, clear_db_artists, clear_db_tracks
from file_utilities import (
    read_genres,
    read_artist_csv,
    read_track_csv,
    write_csv_header,
    write_csv,
    clear_file,
)
import logging

logger = logging.getLogger()
ARTIST_HEADERS = [
    "name",
    "id",
]
ALBUM_HEADERS = [
    "id",
]
TRACK_HEADERS = [
    "name",
    "id",
    "artists",
]


class SixDegrees:
    """Class to handle functionality between Neo4j and Spotify APIs"""

    def __init__(self: "SixDegrees") -> None:
        self._spotify = SpotifyClient()
        self._genres = read_genres("data/genres.json")
        self._artists = []
        self._albums = []
        self._tracks = []

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
        for i, genre in enumerate(self._genres):
            offset = 0
            logger.info(
                "Scraping artists for genre %s/%s", i + 1, len(self._genres)
            )
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
        write_csv_header("data/artists.csv", ARTIST_HEADERS)
        final_artists = []
        for artist in self._artists:
            artist_id = artist["id"]
            if (
                artist_id not in [a["id"] for a in final_artists]
                and artist["popularity"] >= 40
            ):
                final_artists.append({"name": artist["name"], "id": artist_id})
        self._artists = final_artists
        write_csv("data/artists.csv", self._artists, ARTIST_HEADERS)

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
        clear_file("data/artists.csv")
        self.scrape_artists()
        self.filter_artists()
        self.create_artists()

    def import_artists(self: "SixDegrees") -> None:
        """Imports artists from the id file

        Args:
            self (SixDegrees): Instance of SixDegrees
        """
        self._artists = read_artist_csv("data/artists.csv")
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

    def scrape_tracks(self: "SixDegrees") -> None:
        """Scrapes tracks for a given list of albums

        Args:
            self (SixDegrees): Instance of SixDegrees
        """
        tracks = []
        for i in range(0, len(self._albums), 20):
            logger.info("Scraping tracks %s/%s", i, len(self._albums))
            album_ids = [album["id"] for album in self._albums[i : i + 20]]
            tracks += [
                album["tracks"]["items"]
                for album in self._spotify.albums(albums=album_ids)["albums"]
            ]
        tracks = [track for album in tracks for track in album]
        self._tracks += tracks

    def filter_tracks(self: "SixDegrees") -> None:
        """Filters tracks based on artist collaborations. Only one
        collaboration per artist pair is allowed

        Args:
            self (SixDegrees): Instance of SixDegrees
        """
        write_csv_header("data/tracks.csv", TRACK_HEADERS)
        collabs = set()
        filtered_tracks = []
        for i, track in enumerate(self._tracks):
            logger.info("Filtering tracks %s/%s", i + 1, len(self._tracks))
            track_id = track["id"]
            included_artists = [
                {"name": artist["name"], "id": artist["id"]}
                for artist in track["artists"]
                if any(a.get("id") == artist["id"] for a in self._artists)
            ]
            if len(included_artists) == 0 or len(included_artists) == 1:
                continue
            track_conns = set()
            for i, artist_i in enumerate(included_artists):
                for artist_j in included_artists[i + 1 :]:
                    conn = tuple(sorted([artist_i["id"], artist_j["id"]]))
                    track_conns.add(conn)
            if len(track_conns.intersection(collabs)) == 0 and all(
                track_id != t["id"] for t in filtered_tracks
            ):
                collabs.update(track_conns)
                filtered_tracks.append(
                    {
                        "name": track["name"],
                        "id": track_id,
                        "artists": [
                            artist["id"] for artist in included_artists
                        ],
                    }
                )
        self._tracks = filtered_tracks
        write_csv("data/tracks.csv", self._tracks, TRACK_HEADERS)

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
        clear_file("data/tracks.csv")
        self._artists = read_artist_csv("data/artists.csv")
        for i, artist in enumerate(self._artists):
            logger.info(
                "Scraping albums for artist %s/%s", i + 1, len(self._artists)
            )
            albums = self.scrape_albums(artist["id"])
            self._albums += albums
        self.scrape_tracks()
        self.filter_tracks()
        self.create_tracks()

    def import_tracks(self: "SixDegrees") -> None:
        """Imports tracks from the id file

        Args:
            self (SixDegrees): Instance of SixDegrees
        """
        self._tracks = read_track_csv("data/tracks.csv")
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

    def find_path(self: "SixDegrees", start: str, end: str) -> list:
        """Finds the shortest path between two artists

        Args:
            self (SpotifyClient): Instance of SpotifyClient
            start (str): Starting artist name
            end (str): Ending artist name

        Returns:
            list: The shortest path between two artists
        """
        starting_id = self._spotify.search(
            q=start, cat="artist", limit=1, offset=0
        )["artists"]["items"][0]["id"]
        ending_id = self._spotify.search(
            q=end, cat="artist", limit=1, offset=0
        )["artists"]["items"][0]["id"]
        with Neo4jClient() as neo4j_manager:
            return neo4j_manager.shortest_path(starting_id, ending_id)

    def clear_db(self: "SixDegrees") -> None:
        """Clears the Neo4j database

        Args:
            self (SixDegrees): Instance of SixDegrees
        """
        clear_db_artists()
        clear_db_tracks()
