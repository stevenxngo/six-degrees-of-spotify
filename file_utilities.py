import os


def clear_files(path):
    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)
        print(file_path)
        if os.path.isfile(file_path):
            with open(file_path, "w", encoding="utf-8") as file:
                file.truncate()


def write_name_id(path, item):
    with open(path, "a", encoding="utf-8") as file:
        file.write(item["name"] + " | " + item["id"] + "\n")


def write_to_file(path, val):
    with open(path, "a", encoding="utf-8") as file:
        file.write(val + "\n")


def read_genres(path):
    genres = []
    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            genres.append(line.strip())
    return genres


def read_ids(path):
    ids = set()
    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            ids.add(line.strip())
    return ids
