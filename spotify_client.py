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
        self.sp = spotipy.Spotify(auth_manager=auth_manager)

    def get_artist(self: "SpotifyClient", artist_id: str) -> dict:
        return self.sp.artist(artist_id=artist_id)