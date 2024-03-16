from six_degrees import SixDegrees
from logging_config import configure_logger

def main() -> None:
    configure_logger()
    six_degrees = SixDegrees()
    six_degrees.verify_conn()
    six_degrees.initialize_tracks()

if __name__ == "__main__":
    main()
