import os
from dotenv import load_dotenv
from typing import Any
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy

load_dotenv()


class SpotifyClient:
    """Spotify class to handle spotify API requests"""

    def __init__(self: "SpotifyClient") -> None:
        client_id = os.getenv("SPOTIFY_CLIENT_ID")
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        auth_manager = SpotifyClientCredentials(
            client_id=client_id, client_secret=client_secret
        )
        self._spotify = spotipy.Spotify(auth_manager=auth_manager)

    def get_artist(self: "SpotifyClient", artist_id: str) -> Any:
        """Gets artist information from Spotify API

        Args:
            self (SpotifyClient): Instance of SpotifyClient
            artist_id (str): The artist id

        Returns:
            dict: Artist information
        """
        return self._spotify.artist(artist_id=artist_id)

    def search(
        self: "SpotifyClient", q: str, cat: str, limit: int, offset: int
    ) -> Any:
        """Searches Spotify API for artists, albums, or tracks

        Args:
            self (SpotifyClient): Instance of SpotifyClient
            q (str): The search query
            cat (str): The category to search
            limit (int): The number of results to return
            offset (int): The offset for the search

        Returns:
            dict: The search results
        """
        return self._spotify.search(q=q, type=cat, limit=limit, offset=offset)

    def artists(self: "SpotifyClient", artists: list) -> Any:
        """Gets artist information from Spotify API

        Args:
            self (SpotifyClient): Instance of SpotifyClient
            artists (list): The artist ids

        Returns:
            dict: Artist information
        """
        return self._spotify.artists(artists=artists)

    def artist_albums(
        self: "SpotifyClient",
        artist_id: str,
        album_type: str,
        limit: int = 20,
        offset: int = 0,
    ) -> Any:
        """Gets albums for a given artist

        Args:
            self (SpotifyClient): Instance of SpotifyClient
            artist_id (str): The artist id
            album_type (str): The type of album
            limit (int, optional): The number of albums to return. Defaults
            to 20.
            offset (int, optional): The offset for albums. Defaults to 0.

        Returns:
            dict: The albums
        """
        return self._spotify.artist_albums(
            artist_id=artist_id,
            album_type=album_type,
            limit=limit,
            offset=offset,
        )

    def album_tracks(
        self: "SpotifyClient", album_id: str, limit: int = 50, offset: int = 0
    ) -> Any:
        """Gets tracks for a given album

        Args:
            self (SpotifyClient): Instance of SpotifyClient
            album_id (str): The album id
            limit (int, optional): The number of tracks to return. Defaults
            to 50.
            offset (int, optional): The offset for tracks. Defaults to 0.

        Returns:
            dict: The tracks
        """
        return self._spotify.album_tracks(
            album_id=album_id, limit=limit, offset=offset
        )

    def albums(self: "SpotifyClient", albums: list) -> Any:
        """Gets album information from Spotify API

        Args:
            self (SpotifyClient): Instance of SpotifyClient
            albums (list): The album ids

        Returns:
            dict: Album information
        """
        return self._spotify.albums(albums=albums)
