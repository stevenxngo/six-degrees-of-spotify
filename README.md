# Six Degrees of Spotify (WIP)

Note: This project is a work in progress and is not yet complete.

## Description

This project is an application that enables users to find the shortest path between two artists through collaborations, if possible under 6 degrees. It uses data provided by the [Spotify API](https://developer.spotify.com/documentation/web-api) to retrieve data about artists and their tracks. All data scraped from Spotify is stored in a [Neo4j](https://neo4j.com/) database, which is then used to find the shortest path between two artists. The current implementation supports the top 250 artists of a [popularity](https://developer.spotify.com/documentation/web-api/reference/get-an-artist#:~:text=of%20the%20artist.-,popularity,-integer) over 40 from the following genres: 

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
2. Enter the names of the two artists you want to find the shortest path between (Note: names must be spelled correctly and are case-sensitive)
3. The application will then find the shortest path between the two artists and display it to the user

## Common Issues

If initializing the database is taking too long, you may be encountering [Spotify's rate limits](https://developer.spotify.com/documentation/web-api/concepts/rate-limits). Please wait a few minutes and try again.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details