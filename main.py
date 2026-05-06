import argparse
from six_degrees import SixDegrees
from logging_config import configure_logger


def confirm(prompt: str) -> bool:
    return input(f"{prompt} (y/n): ").lower() == "y"


def main(args: argparse.Namespace) -> None:
    configure_logger(verbose=args.verbose)
    sd = SixDegrees()

    if args.init:
        if confirm(
            "Initialize database? "
            "Warning: this will override all csv files and the database"
        ):
            sd.initialize_data()
    elif args.seed:
        sd.initialize_seed_artists()
    elif args.update:
        sd.update_data()
    elif args.artists:
        sd.import_artists()
        sd.initialize_albums()
        sd.initialize_tracks()
        sd.create_relationships()
    elif args.tracks:
        sd.import_albums()
        sd.initialize_tracks()
        sd.create_relationships()
    elif args.imprt:
        if confirm(
            "Import database from csv files? "
            "Warning: this will override the current database"
        ):
            sd.import_data()
    elif args.stats:
        sd.print_stats()
    elif args.debug:
        sd.verify_conn()
    elif args.clear:
        if confirm("Clear the database?"):
            sd.clear_db()
    else:
        start = input("Starting artist name: ")
        end = input("Ending artist name: ")
        sd.find_path(start, end)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Six Degrees of Spotify")
    parser.add_argument(
        "-i",
        "--init",
        action="store_true",
        help=(
            "Full initialization from Spotify API"
            " (artists + albums + tracks)"
        ),
    )
    parser.add_argument(
        "-s",
        "--seed",
        action="store_true",
        help="Resolve artists from seeds.json and merge into artists.csv",
    )
    parser.add_argument(
        "-u",
        "--update",
        action="store_true",
        help=(
            "Incrementally scrape albums/tracks for new artists only,"
            " then update the database"
        ),
    )
    parser.add_argument(
        "-a",
        "--artists",
        action="store_true",
        help="Import artists from artists.csv, then scrape albums and tracks",
    )
    parser.add_argument(
        "-t",
        "--tracks",
        action="store_true",
        help="Resume track scraping from existing albums.csv",
    )
    parser.add_argument(
        "-m",
        "--imprt",
        action="store_true",
        help="Import all data from csv files into the database",
    )
    parser.add_argument(
        "--stats", action="store_true", help="Print database statistics"
    )
    parser.add_argument(
        "-d", "--debug", action="store_true", help="Verify database connection"
    )
    parser.add_argument(
        "-c", "--clear", action="store_true", help="Clear the database"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    args = parser.parse_args()
    main(args)
