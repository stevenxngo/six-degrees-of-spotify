import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()


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

    def verify_conn(self: "Neo4jClient") -> None:
        self.driver.verify_connectivity()

    def create_artist_node(self: "Neo4jClient", artist: dict) -> None:
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
