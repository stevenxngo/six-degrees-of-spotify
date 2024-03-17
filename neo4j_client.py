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
        self._driver = None

    def __enter__(self):
        uri = os.getenv("NEO4J_URI")
        username = os.getenv("NEO4J_USERNAME")
        password = os.getenv("NEO4J_PASSWORD")
        self._driver = GraphDatabase.driver(uri, auth=(username, password))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._driver.close()

    def clear_graph(self: "Neo4jClient") -> None:
        """Clears the Neo4j database

        Args:
            self (Neo4jClient): Instance of Neo4jClient
        """
        with self._driver.session() as session:
            delete_query = "MATCH (n) DETACH DELETE n"
            session.run(delete_query)

    def clear_artists(self: "Neo4jClient") -> None:
        """Clears the artist nodes from the Neo4j database

        Args:
            self (Neo4jClient): Instance of Neo4jClient
        """
        with self._driver.session() as session:
            delete_query = "MATCH (n: Artist) DETACH DELETE n"
            session.run(delete_query)

    def clear_tracks(self: "Neo4jClient") -> None:
        """Clears the track nodes from the Neo4j database

        Args:
            self (Neo4jClient): Instance of Neo4jClient
        """
        with self._driver.session() as session:
            delete_query = "MATCH (n: Track) DETACH DELETE n"
            session.run(delete_query)

    def verify_conn(self: "Neo4jClient") -> None:
        """Verifies connection to Neo4j database

        Args:
            self (Neo4jClient): Instance of Neo4jClient
        """
        self._driver.verify_connectivity()

    def create_artist_node(self: "Neo4jClient", artist: dict) -> None:
        """Creates an artist node in the Neo4j database

        Args:
            self (Neo4jClient): Instance of Neo4jClient
            artist (dict): The artist information
        """
        with self._driver.session() as session:
            constraint = (
                "CREATE CONSTRAINT unique_artist_id IF NOT EXISTS "
                "FOR (n: Artist) REQUIRE n.id IS UNIQUE"
            )
            session.run(constraint)

            node_query = "MERGE (n:Artist {name: $name, id: $id})"

            session.run(
                node_query,
                name=artist["name"],
                id=artist["id"],
            )

    def create_track_node(self: "Neo4jClient", track: dict) -> None:
        """Creates a track node in the Neo4j database

        Args:
            self (Neo4jClient): Instance of Neo4jClient
            track (dict): The track information
        """
        with self._driver.session() as session:
            unique_track_constraint = (
                "CREATE CONSTRAINT unique_track_id IF NOT EXISTS "
                "FOR (n: Track) REQUIRE n.id IS UNIQUE"
            )
            session.run(unique_track_constraint)

            node_query = "MERGE (n:Track {name: $name, id: $id, artists: $artists})"
            artists = [artist["id"] for artist in track["artists"]]
            session.run(
                node_query,
                name=track["name"],
                id=track["id"],
                artists=artists,
            )

    def create_relationships(self: "Neo4jClient") -> None:
        """Creates relationships between artists and tracks in the Neo4j
        database

        Args:
            self (Neo4jClient): Instance of Neo4jClient
        """
        with self._driver.session() as session:
            relationship_query = (
                "MATCH (a: Artist), (t: Track) "
                "WHERE a.id IN t.artists "
                "MERGE (a)-[:APPEARS_ON]->(t)"
            )
            session.run(relationship_query)

    def shortest_path(self: "Neo4jClient", start_id: str, end_id: str) -> list:
        """Finds the shortest path between two artists, if it exists

        Args:
            self (Neo4jClient): Instance of Neo4jClient
            start_id (str): id of the starting artist
            end_id (str): id of the ending artist

        Returns:
            list: The shortest path between the two artists
        """
        with self._driver.session() as session:
            path_query = (
                "MATCH (start:Artist {id: $start_id}), (end:Artist {id: $end_id}), "
                "p = shortestPath((start)-[:APPEARS_ON*]-(end)) "
                "UNWIND nodes(p) AS node "
                "RETURN node.id, node.name"
            )
            result = session.run(path_query, start_id=start_id, end_id=end_id)
            path = []

            if result.peek() is None:
                print("No path found")
                return path
            print("Path found")
            for record in result:
                node_id = record["node.id"]
                path.append(node_id)
            return path
