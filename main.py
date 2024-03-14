from spotify import SpotifyClient

def main():
    spotify_client = SpotifyClient()
    artist = spotify_client.get_artist("6HvZYsbFfjnjFrWF950C9d")
    print(artist)


if __name__ == "__main__":
    main()
