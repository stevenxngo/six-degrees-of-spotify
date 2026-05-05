from spotify_client import SpotifyClient
from neo4j_client import Neo4jClient, clear_db_artists, clear_db_tracks
from file_utilities import (
    read_genres,
    read_artist_csv,
    read_album_csv,
    read_track_csv,
    write_csv_header,
    write_csv,
    clear_file,
)
import json
import logging
import os
import time
from requests.exceptions import ReadTimeout

ARTISTS_OFFSET_PATH = "data/artists_offset.txt"
ARTISTS_RAW_PATH = "data/artists_raw.jsonl"
ALBUMS_OFFSET_PATH = "data/albums_offset.txt"
ALBUMS_RAW_PATH = "data/albums_raw.jsonl"
TRACKS_OFFSET_PATH = "data/tracks_offset.txt"
TRACKS_RAW_PATH = "data/tracks_raw.jsonl"

logger = logging.getLogger()
ARTIST_HEADERS = [
    "name",
    "id",
]
ALBUM_HEADERS = [
    "name",
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
        """Scrapes the top 50 artists for each genre

        Args:
            self (SixDegrees): Instance of SixDegrees
        """
        limit = 50
        for i, genre in enumerate(self._genres):
            offset = 0
            logger.info(
                "Scraping artists for genre %s/%s", i + 1, len(self._genres)
            )
            for _ in range(1):
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
        clear_file("data/artists.csv")
        write_csv_header("data/artists.csv", ARTIST_HEADERS)
        final_artists = []
        for artist in self._artists:
            artist_id = artist["id"]
            if (
                artist_id not in [a["id"] for a in final_artists]
                and artist.get("popularity", 100) >= 40
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
            neo4j_client.setup_constraints()
            neo4j_client.create_artist_nodes(self._artists)

    def scrape_seed_artists(self: "SixDegrees") -> None:
        """Resolves artist names from seeds.json via search and adds them
        to the artist list.

        Args:
            self (SixDegrees): Instance of SixDegrees
        """
        seed_names = read_genres("data/seeds.json")
        seed_ids = []

        start_i = 0
        if os.path.exists(ARTISTS_OFFSET_PATH):
            with open(ARTISTS_OFFSET_PATH) as f:
                content = f.read().strip()
            if content:
                start_i = int(content)
                if os.path.exists(ARTISTS_RAW_PATH):
                    with open(ARTISTS_RAW_PATH, encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                seed_ids.append(json.loads(line)["id"])
                logger.info(
                    "Resuming seed scraping from %s/%s (%s ids loaded)",
                    start_i,
                    len(seed_names),
                    len(seed_ids),
                )

        with open(ARTISTS_RAW_PATH, "a", encoding="utf-8") as raw_file:
            for i in range(start_i, len(seed_names)):
                name = seed_names[i]
                logger.info(
                    "Resolving seed %s/%s: %s", i + 1, len(seed_names), name
                )
                results = self._spotify.search(
                    q=name, cat="artist", limit=1, offset=0
                )
                items = results["artists"]["items"]
                if items:
                    artist_id = items[0]["id"]
                    seed_ids.append(artist_id)
                    raw_file.write(json.dumps({"id": artist_id}) + "\n")
                with open(ARTISTS_OFFSET_PATH, "w") as f:
                    f.write(str(i + 1))

        for i in range(0, len(seed_ids), 50):
            batch = self._spotify.artists(seed_ids[i : i + 50])
            self._artists.extend(a for a in batch["artists"] if a)

        for path in [ARTISTS_OFFSET_PATH, ARTISTS_RAW_PATH]:
            if os.path.exists(path):
                os.remove(path)

        logger.info("Added %s seed artists", len(seed_ids))

    def initialize_artists(self: "SixDegrees") -> None:
        """Initializes the artists data using Spotify API

        Args:
            self (SixDegrees): Instance of SixDegrees
        """
        self.scrape_artists()
        self.filter_artists()
        self.create_artists()

    def initialize_seed_artists(self: "SixDegrees") -> None:
        """Resolves seeds.json and merges results into the existing
        artists.csv. Does not redo album or track scraping.

        Args:
            self (SixDegrees): Instance of SixDegrees
        """
        if os.path.exists("data/artists.csv"):
            self._artists.extend(read_artist_csv("data/artists.csv"))
        self.scrape_seed_artists()
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
            for attempt in range(5):
                try:
                    albums = self._spotify.artist_albums(
                        artist_id=artist_id,
                        album_type="album,single",
                        limit=limit,
                        offset=offset,
                    )
                    break
                except ReadTimeout:
                    if attempt == 4:
                        raise
                    wait = 2**attempt
                    logger.warning(
                        "Timeout scraping albums, retrying in %ss (%s/5)",
                        wait,
                        attempt + 2,
                    )
                    time.sleep(wait)
                except Exception as e:
                    logger.warning(
                        "Error scraping albums for %s: %s, skipping",
                        artist_id,
                        e,
                    )
                    return discography
            discography += albums["items"]
            if albums["next"]:
                offset += limit
            else:
                break
        return discography

    def scrape_tracks(self: "SixDegrees") -> None:
        """Scrapes tracks for a given list of albums, with retry and
        checkpoint support. If a previous run was interrupted, it resumes
        from the last saved offset.

        Args:
            self (SixDegrees): Instance of SixDegrees
        """
        start_i = 0
        if os.path.exists(TRACKS_OFFSET_PATH):
            with open(TRACKS_OFFSET_PATH) as f:
                content = f.read().strip()
            if content:
                start_i = int(content)
                if os.path.exists(TRACKS_RAW_PATH):
                    with open(TRACKS_RAW_PATH, encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                self._tracks.append(json.loads(line))
                logger.info(
                    "Resuming track scraping from album %s/%s (%s tracks loaded)",
                    start_i,
                    len(self._albums),
                    len(self._tracks),
                )

        with open(TRACKS_RAW_PATH, "a", encoding="utf-8") as raw_file:
            for i in range(start_i, len(self._albums), 20):
                logger.info("Scraping tracks %s/%s", i, len(self._albums))
                album_ids = [album["id"] for album in self._albums[i : i + 20]]
                for attempt in range(5):
                    try:
                        result = self._spotify.albums(albums=album_ids)[
                            "albums"
                        ]
                        break
                    except ReadTimeout:
                        if attempt == 4:
                            raise
                        wait = 2**attempt
                        logger.warning(
                            "Timeout scraping tracks, retrying in %ss (%s/5)",
                            wait,
                            attempt + 2,
                        )
                        time.sleep(wait)
                for album in result:
                    if album:
                        for track in album["tracks"]["items"]:
                            compact = {
                                "id": track["id"],
                                "name": track["name"],
                                "artists": [
                                    {"id": a["id"], "name": a["name"]}
                                    for a in track["artists"]
                                ],
                            }
                            self._tracks.append(compact)
                            raw_file.write(json.dumps(compact) + "\n")
                with open(TRACKS_OFFSET_PATH, "w") as f:
                    f.write(str(i + 20))

        for path in [TRACKS_OFFSET_PATH, TRACKS_RAW_PATH]:
            if os.path.exists(path):
                os.remove(path)

    def filter_tracks(self: "SixDegrees") -> None:
        """Filters tracks based on artist collaborations. Only one
        collaboration per artist pair is allowed, preferring the most
        popular track when multiple options exist.

        Args:
            self (SixDegrees): Instance of SixDegrees
        """
        write_csv_header("data/tracks.csv", TRACK_HEADERS)
        artist_ids = {a["id"] for a in self._artists}

        seen_ids = set()
        candidates = []
        for track in self._tracks:
            track_id = track["id"]
            if track_id in seen_ids:
                continue
            included_artists = [
                {"name": artist["name"], "id": artist["id"]}
                for artist in track["artists"]
                if artist["id"] in artist_ids
            ]
            if len(included_artists) <= 1:
                continue
            seen_ids.add(track_id)
            candidates.append((track, included_artists))

        logger.info(
            "Fetching popularity for %s candidate tracks", len(candidates)
        )
        popularity = {}
        for i in range(0, len(candidates), 50):
            batch_ids = [t["id"] for t, _ in candidates[i : i + 50]]
            results = self._spotify.tracks(batch_ids)
            logger.info(
                "Fetched popularity for tracks %s/%s",
                min(i + 50, len(candidates)),
                len(candidates),
            )
            for t in results["tracks"]:
                if t:
                    popularity[t["id"]] = t["popularity"]

        candidates.sort(
            key=lambda x: popularity.get(x[0]["id"], 0), reverse=True
        )

        collabs = set()
        filtered_tracks = []
        for i, (track, included_artists) in enumerate(candidates):
            logger.info("Filtering tracks %s/%s", i + 1, len(candidates))
            track_conns = set()
            for j, artist_i in enumerate(included_artists):
                for artist_j in included_artists[j + 1 :]:
                    conn = tuple(sorted([artist_i["id"], artist_j["id"]]))
                    track_conns.add(conn)
            if not track_conns.intersection(collabs):
                collabs.update(track_conns)
                filtered_tracks.append(
                    {
                        "name": track["name"],
                        "id": track["id"],
                        "artists": [a["id"] for a in included_artists],
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
            neo4j_client.setup_constraints()
            neo4j_client.create_track_nodes(self._tracks)

    def initialize_albums(self: "SixDegrees") -> None:
        """Scrapes albums for all artists and saves to albums.csv

        Args:
            self (SixDegrees): Instance of SixDegrees
        """
        self._artists = read_artist_csv("data/artists.csv")

        start_i = 0
        if os.path.exists(ALBUMS_OFFSET_PATH):
            with open(ALBUMS_OFFSET_PATH) as f:
                content = f.read().strip()
            if content:
                start_i = int(content)
                if os.path.exists(ALBUMS_RAW_PATH):
                    with open(ALBUMS_RAW_PATH, encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                self._albums.append(json.loads(line))
                logger.info(
                    "Resuming album scraping from artist %s/%s (%s albums loaded)",
                    start_i,
                    len(self._artists),
                    len(self._albums),
                )
        else:
            clear_file("data/albums.csv")
            for path in [TRACKS_OFFSET_PATH, TRACKS_RAW_PATH]:
                if os.path.exists(path):
                    os.remove(path)

        with open(ALBUMS_RAW_PATH, "a", encoding="utf-8") as raw_file:
            for i in range(start_i, len(self._artists)):
                artist = self._artists[i]
                logger.info(
                    "Scraping albums for artist %s/%s", i + 1, len(self._artists)
                )
                albums = self.scrape_albums(artist["id"])
                for album in albums:
                    compact = {
                        "id": album["id"],
                        "name": album["name"],
                        "release_date": album.get("release_date", "0000"),
                    }
                    self._albums.append(compact)
                    raw_file.write(json.dumps(compact) + "\n")
                with open(ALBUMS_OFFSET_PATH, "w") as f:
                    f.write(str(i + 1))

        seen = set()
        self._albums = [
            a
            for a in self._albums
            if not (a["id"] in seen or seen.add(a["id"]))
            and a.get("release_date", "0000")[:4] >= "2000"
        ]
        write_csv_header("data/albums.csv", ALBUM_HEADERS)
        write_csv(
            "data/albums.csv",
            [{"name": a["name"], "id": a["id"]} for a in self._albums],
            ALBUM_HEADERS,
        )

        for path in [ALBUMS_OFFSET_PATH, ALBUMS_RAW_PATH]:
            if os.path.exists(path):
                os.remove(path)

        logger.info("Saved %s albums to albums.csv", len(self._albums))

    def import_albums(self: "SixDegrees") -> None:
        """Imports albums from albums.csv

        Args:
            self (SixDegrees): Instance of SixDegrees
        """
        self._albums = read_album_csv("data/albums.csv")
        self._artists = read_artist_csv("data/artists.csv")
        logger.info("Loaded %s albums from albums.csv", len(self._albums))

    def initialize_tracks(self: "SixDegrees") -> None:
        """Scrapes tracks from self._albums and saves to tracks.csv.
        Call initialize_albums or import_albums first.

        Args:
            self (SixDegrees): Instance of SixDegrees
        """
        clear_file("data/tracks.csv")
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
        self.create_relationships()

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
        self.initialize_albums()
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

    def find_path(self: "SixDegrees", start: str, end: str) -> None:
        """Finds and prints the shortest path between two artists

        Args:
            self (SixDegrees): Instance of SixDegrees
            start (str): Starting artist name
            end (str): Ending artist name
        """
        start_results = self._spotify.search(
            q=start, cat="artist", limit=1, offset=0
        )["artists"]["items"]
        end_results = self._spotify.search(
            q=end, cat="artist", limit=1, offset=0
        )["artists"]["items"]
        if not start_results:
            print(f"Artist not found: {start}")
            return
        if not end_results:
            print(f"Artist not found: {end}")
            return
        starting_id = start_results[0]["id"]
        ending_id = end_results[0]["id"]
        with Neo4jClient() as neo4j_manager:
            path = neo4j_manager.shortest_path(starting_id, ending_id)
        if not path:
            print("No path found between these two artists.")
            return
        degrees = sum(1 for node in path if node["type"] == "artist") - 1
        print(f"\n{degrees} degree(s) of separation:\n")
        for node in path:
            if node["type"] == "artist":
                print(f"  Artist: {node['name']}")
            else:
                print(f"    via \"{node['name']}\"")

    def print_stats(self: "SixDegrees") -> None:
        """Prints database statistics to the console

        Args:
            self (SixDegrees): Instance of SixDegrees
        """
        with Neo4jClient() as neo4j_client:
            stats = neo4j_client.db_stats()
            connected = neo4j_client.most_connected_artists()
            prolific = neo4j_client.most_prolific_artists()
            collabs = neo4j_client.biggest_collabs()
            print("\nComputing approximate diameter (sampling 200 pairs)...")
            diameter = neo4j_client.longest_path()

        print("\n=== Database Summary ===")
        print(f"  Artists:       {stats['artists']}")
        print(f"  Tracks:        {stats['tracks']}")
        print(f"  Relationships: {stats['relationships']}")
        print(f"  Isolated:      {stats['isolated']} (no collaborations)")

        print("\n=== Artists with Most Collaborators ===")
        for i, a in enumerate(connected, 1):
            print(f"  {i:2}. {a['name']} — {a['collaborators']} collaborators")

        print("\n=== Artists with Most Collaborations ===")
        for i, a in enumerate(prolific, 1):
            print(f"  {i:2}. {a['name']} — {a['tracks']} tracks")

        print("\n=== Tracks with Most Collaborators ===")
        for i, t in enumerate(collabs, 1):
            print(f"  {i:2}. \"{t['name']}\" — {t['artists']} artists")

        print("\n=== Approximate Diameter (longest shortest path) ===")
        if diameter:
            print(
                f"  {diameter['degrees']} degree(s): {diameter['start']} → {diameter['end']}"
            )
            for node in diameter["path"]:
                if node["type"] == "artist":
                    print(f"    Artist: {node['name']}")
                else:
                    print(f"      via \"{node['name']}\"")
        else:
            print("  No connected pairs found.")
        print()

    def clear_db(self: "SixDegrees") -> None:
        """Clears the Neo4j database

        Args:
            self (SixDegrees): Instance of SixDegrees
        """
        clear_db_artists()
        clear_db_tracks()
