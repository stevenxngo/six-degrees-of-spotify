import os
import csv


def clear_file(path: str) -> None:
    """Clears the files in a directory

    Args:
        path (str): The path to the directory
    """
    if os.path.isfile(path):
        with open(path, "w", encoding="utf-8") as _:
            pass


def write_csv_header(path: str, header: list[str]) -> None:
    """Writes a header to a CSV file

    Args:
        path (str): The path to the file
        header (list[str]): The header to write
    """
    with open(path, "a", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=header)
        writer.writeheader()


def write_csv(path: str, data: list[dict], headers: list[str]) -> None:
    """Writes data to a CSV file

    Args:
        path (str): The path to the file
        data (list[dict]): The data to write
    """
    with open(path, "a", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writerows(data)


def read_genres(path: str) -> list[str]:
    """Reads genres from a file

    Args:
        path (str): The path to the file

    Returns:
        list[str]: The genres
    """
    genres = []
    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            genres.append(line.strip())
    return genres


def read_ids(path: str) -> set[str]:
    """Reads ids from a file

    Args:
        path (str): The path to the file

    Returns:
        set[str]: The ids
    """
    ids = set()
    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            ids.add(line.strip())
    return ids


def read_csv(path: str) -> list[dict]:
    """Reads data from a CSV file

    Args:
        path (str): The path to the file

    Returns:
        list[dict]: The data
    """
    data = []
    with open(path, "r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
        # Append a dictionary representing each row to the 'data' list
            data.append({'name': row['name'], 'id': row['id']})
    return data
