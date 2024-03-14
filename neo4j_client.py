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
