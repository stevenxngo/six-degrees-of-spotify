# Six Degrees of Spotify (WIP)

Note: This project is a work in progress and is not yet complete.

## Description

This project is an application that enables users to find the shortest path between two artists through collaborations, if possible under 6 degrees. It uses data provided by the [Spotify API](https://developer.spotify.com/documentation/web-api) to retrieve data about artists and their tracks. All data scraped from Spotify is stored in a [Neo4j](https://neo4j.com/) database, which is then used to find the shortest path between two artists. The current implementation supports the top 50 artists of a [popularity](https://developer.spotify.com/documentation/web-api/reference/get-an-artist#:~:text=of%20the%20artist.-,popularity,-integer) from the following genres: 

* dance
* dubstep
* edm
* electro
* electronic
* hip-hop
* house
* indie
* indie-pop
* k-pop
* pop
* progressive-house
* r-n-b

## Pre-requisites

* [Python 3.10](https://www.python.org/downloads/release/python-3100/)
* [Neo4j Account](https://neo4j.com/cloud/platform/aura-graph-database/?ref=nav-get-started-cta)
* [Spotify Developer Account](https://developer.spotify.com/)

## Database Initialization

There are two ways to initialize the database:

1. Run the `main.py` with the `-i` or `--init` flag to initialize the database using Spotify's API. This is the recommended method if you want the most up-to-date data. **Warning**: This will take a long time to run, as it will need to make a large number of requests to Spotify's API to retrieve the data and will override both the `artists.csv` and `tracks.csv` files, as well as clear the database. 

2. Run the `main.py` with the `-m` or `--imprt` flag to initialize the database using the pre-existing artists and tracks csv file. This will be much faster than the first method, but the data will not be as up-to-date. This is the recommended method if you want to test the application without waiting for all the data to be retrieved. The current csv files up to date as of 2024-03-17. **Warning**: This will clear the database, in order to re-initialize it with the csv files.

**Warning**: The database will be cleared before initializing the database using either method. The csv files will also be overridden if the first method is used.

## Installation

1. Clone the repository
2. Install the required packages using `pip install -r requirements.txt`
3. Create a `.env` file in the root directory of the project and add the following environment variables:

```
SPOTIFY_CLIENT_ID=<your_spotify_client_id>
SPOTIFY_CLIENT_SECRET=<your_spotify_client_secret>
NEO4J_URI=<your_neo4j_uri>
NEO4J_USER=<your_neo4j_user>
NEO4J_PASSWORD=<your_neo4j_password>
```

4. Run the `main.py` file

## Usage

1. Run the `main.py` file
2. Enter the names of the two artists you want to find the shortest path between
3. The application will then find the shortest path between the two artists and display it to the user

If you want to initialize the database with genres other than the ones listed above, you can modify the `genres` list in the `main.py` file. A list of all available genres can be found [here](/data/all_genres.json).

## Flags

* `-i` or `--init`: Initialize the database using Spotify's API
* `-m` or `--imprt`: Initialize the database using the pre-existing csv files
* `d` or `--debug`: Enable debug mode (not yet implemented). Currently verifies that connection to the database is successful
* `-c` or `--clear`: Clear the database. **Warning**: This action is irreversible

## Common Issues

If initializing the database is taking too long using the first method, you may be encountering [Spotify's rate limits](https://developer.spotify.com/documentation/web-api/concepts/rate-limits). Please wait a few minutes/hours and try again. Otherwise, you can use the second method to initialize the database using the pre-existing csv files.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details