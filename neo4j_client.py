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
        if uri is None or username is None or password is None:
            raise ValueError("Missing Neo4j environment variables")
        self._driver = GraphDatabase.driver(uri, auth=(username, password))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._driver is not None:
            self._driver.close()

    def clear_graph(self: "Neo4jClient") -> None:
        """Clears the Neo4j database

        Args:
            self (Neo4jClient): Instance of Neo4jClient
        """
        if self._driver is not None:
            with self._driver.session() as session:
                delete_query = "MATCH (n) DETACH DELETE n"
                session.run(delete_query)

    def clear_artists(self: "Neo4jClient") -> None:
        """Clears the artist nodes from the Neo4j database

        Args:
            self (Neo4jClient): Instance of Neo4jClient
        """
        if self._driver is not None:
            with self._driver.session() as session:
                delete_query = "MATCH (n: Artist) DETACH DELETE n"
                session.run(delete_query)

    def clear_tracks(self: "Neo4jClient") -> None:
        """Clears the track nodes from the Neo4j database

        Args:
            self (Neo4jClient): Instance of Neo4jClient
        """
        if self._driver is not None:
            with self._driver.session() as session:
                delete_query = "MATCH (n: Track) DETACH DELETE n"
                session.run(delete_query)

    def verify_conn(self: "Neo4jClient") -> None:
        """Verifies connection to Neo4j database

        Args:
            self (Neo4jClient): Instance of Neo4jClient
        """
        if self._driver is not None:
            try:
                self._driver.verify_connectivity()
                print("Neo4j connection successful.")
            except Exception as e:
                print(f"Neo4j connection failed: {e}")

    def setup_constraints(self: "Neo4jClient") -> None:
        """Creates uniqueness constraints for Artist and Track nodes"""
        if self._driver is not None:
            with self._driver.session() as session:
                session.run(
                    "CREATE CONSTRAINT unique_artist_id IF NOT EXISTS "
                    "FOR (n:Artist) REQUIRE n.id IS UNIQUE"
                )
                session.run(
                    "CREATE CONSTRAINT unique_track_id IF NOT EXISTS "
                    "FOR (n:Track) REQUIRE n.id IS UNIQUE"
                )

    def create_artist_nodes(self: "Neo4jClient", artists: list) -> None:
        """Batch-creates artist nodes in the Neo4j database

        Args:
            self (Neo4jClient): Instance of Neo4jClient
            artists (list): List of artist dicts with name and id
        """
        if self._driver is not None:
            with self._driver.session() as session:
                session.run(
                    "UNWIND $artists AS a MERGE (n:Artist {id: a.id}) SET n.name = a.name",
                    artists=artists,
                )

    def create_track_nodes(self: "Neo4jClient", tracks: list) -> None:
        """Batch-creates track nodes in the Neo4j database

        Args:
            self (Neo4jClient): Instance of Neo4jClient
            tracks (list): List of track dicts with name, id, and artists
        """
        if self._driver is not None:
            with self._driver.session() as session:
                session.run(
                    "UNWIND $tracks AS t MERGE (n:Track {id: t.id}) SET n.name = t.name, n.artists = t.artists",
                    tracks=tracks,
                )

    def create_relationships(self: "Neo4jClient") -> None:
        """Creates relationships between artists and tracks in the Neo4j
        database

        Args:
            self (Neo4jClient): Instance of Neo4jClient
        """
        if self._driver is not None:
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
            list: Dicts with 'id', 'name', 'type' for each node in the path
        """
        if self._driver is not None:
            with self._driver.session() as session:
                path_query = (
                    "MATCH (start:Artist {id: $start_id}), (end:Artist {id: $end_id}), "
                    "p = shortestPath((start)-[:APPEARS_ON*]-(end)) "
                    "UNWIND nodes(p) AS node "
                    "RETURN node.id AS id, node.name AS name, "
                    "CASE WHEN node:Artist THEN 'artist' ELSE 'track' END AS type"
                )
                result = session.run(
                    path_query, start_id=start_id, end_id=end_id
                )
                records = list(result)
                if not records:
                    return []
                return [
                    {"id": r["id"], "name": r["name"], "type": r["type"]}
                    for r in records
                ]
        return []
