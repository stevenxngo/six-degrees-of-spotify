from six_degrees import SixDegrees
from logging_config import configure_logger

def main() -> None:
    configure_logger()
    six_degrees = SixDegrees()
    six_degrees.verify_conn()
    # six_degrees.initialize_tracks()
    # six_degrees.create_relationships()
    # start = input("Starting artist name: ")
    # end = input("Ending artist name: ")
    # six_degrees.find_path(start, end)

if __name__ == "__main__":
    main()
