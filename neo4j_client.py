import os
import random
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

    def db_stats(self: "Neo4jClient") -> dict:
        """Returns summary counts for the database

        Returns:
            dict: artists, tracks, relationships, isolated artist count
        """
        if self._driver is None:
            return {}
        with self._driver.session() as session:
            counts = session.run(
                "MATCH (a:Artist) WITH count(a) AS artists "
                "MATCH (t:Track) WITH artists, count(t) AS tracks "
                "MATCH ()-[r:APPEARS_ON]->() "
                "RETURN artists, tracks, count(r) AS relationships"
            ).single()
            isolated = session.run(
                "MATCH (a:Artist) WHERE NOT (a)-[:APPEARS_ON]->() "
                "RETURN count(a) AS isolated"
            ).single()
        if not counts or not isolated:
            return {}
        return {
            "artists": counts["artists"],
            "tracks": counts["tracks"],
            "relationships": counts["relationships"],
            "isolated": isolated["isolated"],
        }

    def most_connected_artists(
        self: "Neo4jClient", limit: int = 10
    ) -> list[dict]:
        """Returns artists with the most unique collaborators

        Args:
            limit (int): Number of results to return

        Returns:
            list[dict]: name and collaborator count per artist
        """
        if self._driver is None:
            return []
        with self._driver.session() as session:
            result = session.run(
                "MATCH (a:Artist)-[:APPEARS_ON]->(t:Track)<-[:APPEARS_ON]-(b:Artist) "
                "WHERE a <> b "
                "RETURN a.name AS name, count(DISTINCT b) AS collaborators "
                "ORDER BY collaborators DESC LIMIT $limit",
                limit=limit,
            )
            return [
                {"name": r["name"], "collaborators": r["collaborators"]}
                for r in result
            ]

    def most_prolific_artists(
        self: "Neo4jClient", limit: int = 10
    ) -> list[dict]:
        """Returns artists with the most tracks

        Args:
            limit (int): Number of results to return

        Returns:
            list[dict]: name and track count per artist
        """
        if self._driver is None:
            return []
        with self._driver.session() as session:
            result = session.run(
                "MATCH (a:Artist)-[:APPEARS_ON]->(t:Track) "
                "RETURN a.name AS name, count(t) AS tracks "
                "ORDER BY tracks DESC LIMIT $limit",
                limit=limit,
            )
            return [{"name": r["name"], "tracks": r["tracks"]} for r in result]

    def biggest_collabs(self: "Neo4jClient", limit: int = 10) -> list[dict]:
        """Returns tracks with the most artists

        Args:
            limit (int): Number of results to return

        Returns:
            list[dict]: name and artist count per track
        """
        if self._driver is None:
            return []
        with self._driver.session() as session:
            result = session.run(
                "MATCH (a:Artist)-[:APPEARS_ON]->(t:Track) "
                "WITH t, count(a) AS artist_count "
                "WHERE artist_count > 1 "
                "RETURN t.name AS name, artist_count "
                "ORDER BY artist_count DESC LIMIT $limit",
                limit=limit,
            )
            return [
                {"name": r["name"], "artists": r["artist_count"]}
                for r in result
            ]

    def all_artist_ids(self: "Neo4jClient") -> list[str]:
        """Returns all artist IDs in the database"""
        if self._driver is None:
            return []
        with self._driver.session() as session:
            result = session.run("MATCH (a:Artist) RETURN a.id AS id")
            return [r["id"] for r in result]

    def longest_path(self: "Neo4jClient", samples: int = 200) -> dict:
        """Samples random artist pairs to find the approximate longest
        shortest path (diameter).

        Args:
            samples (int): Number of random pairs to try

        Returns:
            dict: start/end artist names and degree count, or None if no paths found
        """
        ids = self.all_artist_ids()
        if len(ids) < 2:
            return {}
        best = {}
        for _ in range(samples):
            a, b = random.sample(ids, 2)
            path = self.shortest_path(a, b)
            if not path:
                continue
            degrees = sum(1 for node in path if node["type"] == "artist") - 1
            candidate = {
                "start": path[0]["name"],
                "end": path[-1]["name"],
                "degrees": degrees,
                "path": path,
            }
            if not best or degrees > best["degrees"]:
                best = candidate
        return best
