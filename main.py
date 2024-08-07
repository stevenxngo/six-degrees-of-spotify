from six_degrees import SixDegrees
from logging_config import configure_logger
import argparse


def main(args: argparse.Namespace) -> None:
    configure_logger()
    six_degrees = SixDegrees()
    # six_degrees.verify_conn()
    if args.init:
        sure = input(
            "Are you sure you want to initialize the database? Warning: this will override the csv files and database (y/n): "
        )
        if sure.lower() == "y":
            six_degrees.initialize_data()
        else:
            print("Database not initialized.")
    elif args.imprt:
        sure = input(
            "Are you sure you want to import the database via csv files? Warning: this will override the current database (y/n): "
        )
        if sure.lower() == "y":
            six_degrees.import_tracks()
        else:
            print("Database not imported.")
    elif args.debug:
        six_degrees.verify_conn()
    elif args.clear:
        sure = input("Are you sure you want to clear the database? (y/n): ")
        if sure.lower() == "y":
            six_degrees.clear_db()
        else:
            print("Database not cleared.")
    else:
        # six_degrees.initialize_artists()
        # six_degrees.import_tracks()
        six_degrees.initialize_tracks()
        # six_degrees.create_relationships()
        # start = input("Starting artist name: ")
        # end = input("Ending artist name: ")
        # six_degrees.find_path(start, end)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--init",
        action="store_true",
        help="Flag to specify initialization from Spotify API",
    )
    parser.add_argument(
        "-m",
        "--imprt",
        action="store_true",
        help="Flag to specify import from .csv files",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Flag to specify debug mode",
    )
    parser.add_argument(
        "-c",
        "--clear",
        action="store_true",
        help="Flag to specify clearing of the database",
    )
    args = parser.parse_args()
    main(args)
