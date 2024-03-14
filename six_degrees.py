from spotify_client import SpotifyClient
from neo4j_client import Neo4jClient
from file_utilities import read_genres, write_name_id, write_to_file, read_ids


class SixDegrees:
    """Class to handle functionality between Neo4j and Spotify APIs"""

    def __init__(self: "SixDegrees") -> None:
        self._spotify = SpotifyClient()
        self._genres = read_genres("data/genres.txt")
        self._artists = []
        self._artist_ids = set()

    def verify_conn(self: "SixDegrees") -> None:
        with Neo4jClient() as neo4j_client:
            neo4j_client.verify_conn()

    def scrape_artists(self: "SixDegrees") -> None:
        limit = 50
        for genre in self._genres:
            offset = 0
            for _ in range(2):
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
        for artist in self._artists:
            write_name_id("data/artists/initial_artists.txt", artist)
            artist_id = artist["id"]
            if artist["popularity"] >= 50:
                self._artists.append(artist)
                self._artist_ids.add(artist_id)
                write_name_id("data/artists/artists.txt", artist)
                write_to_file("data/artists/artist_ids.txt", artist_id)

    def initialize_artists(self: "SixDegrees") -> None:
        self.scrape_artists()
        self.filter_artists()

    def create_artists(self: "SixDegrees") -> None:
        with Neo4jClient() as neo4j_client:
            for artist in self._artists:
                neo4j_client.create_artist_node(artist)

    def import_artists(self: "SixDegrees") -> None:
        self._artist_ids = read_ids("data/artists/artist_ids.txt")
        id_list = list(self._artist_ids)
        num_ids = len(id_list)
        for i in range(0, num_ids, 50):
            chunk = id_list[i : i + 50] if i + 50 <= num_ids else id_list[i:]
            results = self._spotify.artists(chunk)
            self._artists.extend(results["artists"])
        self.create_artists()
