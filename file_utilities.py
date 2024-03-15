import os


def clear_files(path: str) -> None:
    """Clears the files in a directory

    Args:
        path (str): The path to the directory
    """
    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)
        if os.path.isfile(file_path):
            with open(file_path, "w", encoding="utf-8") as file:
                file.truncate()


def write_name_id(path: str, item: dict) -> None:
    """Writes the artist name and id to a file

    Args:
        path (str): The path to the file
        item (dict): The artist information
    """
    with open(path, "a", encoding="utf-8") as file:
        file.write(item["name"] + " | " + item["id"] + "\n")


def write_to_file(path: str, val: str) -> None:
    """Writes a value to a file

    Args:
        path (str): The path to the file
        val (str): The value to write
    """
    with open(path, "a", encoding="utf-8") as file:
        file.write(val + "\n")


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
