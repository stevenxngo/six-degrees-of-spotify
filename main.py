from six_degrees import SixDegrees

def main() -> None:
    six_degrees = SixDegrees()
    six_degrees.verify_conn()
    six_degrees.initialize_tracks()

if __name__ == "__main__":
    main()
