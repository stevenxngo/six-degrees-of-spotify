import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()


def clear_db() -> None:
    """Clears the Neo4j database"""
    with Neo4jClient() as neo4j_client:
        neo4j_client.clear_graph()


def clear_db_artists() -> None:
    """Clears the artist nodes from the Neo4j database"""
    with Neo4jClient() as neo4j_client:
        neo4j_client.clear_artists()


def clear_db_tracks() -> None:
    """Clears the track nodes from the Neo4j database"""
    with Neo4jClient() as neo4j_client:
        neo4j_client.clear_tracks()


class Neo4jClient:
    """Neo4j class to handle neo4j database requests"""

    def __init__(self: "Neo4jClient") -> None:
        self.driver = None

    def __enter__(self):
        uri = os.getenv("NEO4J_URI")
        username = os.getenv("NEO4J_USERNAME")
        password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.close()

    def clear_graph(self: "Neo4jClient") -> None:
        """Clears the Neo4j database

        Args:
            self (Neo4jClient): Instance of Neo4jClient
        """
        with self.driver.session() as session:
            delete_query = "MATCH (n) DETACH DELETE n"
            session.run(delete_query)

    def clear_artists(self: "Neo4jClient") -> None:
        """Clears the artist nodes from the Neo4j database

        Args:
            self (Neo4jClient): Instance of Neo4jClient
        """
        with self.driver.session() as session:
            delete_query = "MATCH (n: Artist) DETACH DELETE n"
            session.run(delete_query)

    def clear_tracks(self: "Neo4jClient") -> None:
        """Clears the track nodes from the Neo4j database

        Args:
            self (Neo4jClient): Instance of Neo4jClient
        """
        with self.driver.session() as session:
            delete_query = "MATCH (n: Track) DETACH DELETE n"
            session.run(delete_query)

    def verify_conn(self: "Neo4jClient") -> None:
        """Verifies connection to Neo4j database

        Args:
            self (Neo4jClient): Instance of Neo4jClient
        """
        self.driver.verify_connectivity()

    def create_artist_node(self: "Neo4jClient", artist: dict) -> None:
        """Creates an artist node in the Neo4j database

        Args:
            self (Neo4jClient): Instance of Neo4jClient
            artist (dict): The artist information
        """
        with self.driver.session() as session:
            constraint = (
                "CREATE CONSTRAINT unique_artist_id IF NOT EXISTS "
                "FOR (n: Artist) REQUIRE n.id IS UNIQUE"
            )
            session.run(constraint)

            node_query = "MERGE (n:Artist {name: $name, id: $id, uri: $uri})"

            session.run(
                node_query,
                name=artist["name"],
                id=artist["id"],
                uri=artist["uri"],
            )

    def create_track_node(self: "Neo4jClient", track: dict) -> None:
        """Creates a track node in the Neo4j database

        Args:
            self (Neo4jClient): Instance of Neo4jClient
            track (dict): The track information
        """
        with self.driver.session() as session:
            unique_track_constraint = (
                "CREATE CONSTRAINT unique_track_id IF NOT EXISTS "
                "FOR (n: Track) REQUIRE n.id IS UNIQUE"
            )
            session.run(unique_track_constraint)

            node_query = "MERGE (n:Track {name: $name, id: $id, uri: $uri, artists: $artists})"
            artists = [artist["id"] for artist in track["artists"]]
            session.run(
                node_query,
                name=track["name"],
                id=track["id"],
                uri=track["uri"],
                artists=artists,
            )

    def create_relationships(self: "Neo4jClient") -> None:
        """Creates relationships between artists and tracks in the Neo4j 
        database

        Args:
            self (Neo4jClient): Instance of Neo4jClient
        """
        with self.driver.session() as session:
            relationship_query = (
                "MATCH (a: Artist), (t: Track) "
                "WHERE a.id IN t.artists "
                "MERGE (a)-[:APPEARS_ON]->(t)"
            )
            session.run(relationship_query)
