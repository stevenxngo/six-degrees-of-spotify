from spotify_client import SpotifyClient
from neo4j_client import Neo4jClient


class SixDegrees:
    """Class to handle functionality between Neo4j and Spotify APIs"""

    def __init__(self: "SixDegrees") -> None:
        self.spotify = SpotifyClient()

    def verify_conn(self: "SixDegrees") -> None:
        with Neo4jClient() as neo4j_client:
            neo4j_client.verify_conn()
