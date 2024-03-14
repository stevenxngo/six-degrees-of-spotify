import os
from dotenv import load_dotenv
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

    def get_artist(self: "SpotifyClient", artist_id: str) -> dict:
        return self._spotify.artist(artist_id=artist_id)

    def search(
        self: "SpotifyClient", q: str, cat: str, limit: int, offset: int
    ) -> dict:
        return self._spotify.search(q=q, type=cat, limit=limit, offset=offset)

    def artists(self: "SpotifyClient", artists: list) -> dict:
        return self._spotify.artists(artists=artists)

    def artist_albums(
        self: "SpotifyClient",
        artist_id: str,
        album_type: str,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        return self._spotify.artist_albums(
            artist_id=artist_id,
            album_type=album_type,
            limit=limit,
            offset=offset,
        )

    def album_tracks(
        self: "SpotifyClient", album_id: str, limit: int = 50, offset: int = 0
    ):
        return self._spotify.album_tracks(
            album_id=album_id, limit=limit, offset=offset
        )
