from pathlib import Path
import csv
from shutil import copyfile, make_archive, rmtree
from os import mkdir, remove
from os.path import getsize


TEMP_DATASET = Path("dataset")
TEMP_ORIGS = TEMP_DATASET / "origs"
TEMP_FANDOMS = TEMP_DATASET / "fandoms"


def to_filename(ids):
    author, page, fanfic, chapter = ids
    return f"{author}_{fanfic}.txt"


def zip_dataset():

    MAX_FILES = 20

    mkdir(TEMP_DATASET)
    mkdir(TEMP_DATASET / "origs")
    mkdir(TEMP_DATASET / "fandoms")

    with open("origs.csv") as f:
        origs = set(to_filename(ids) for ids in csv.reader(f))
        # print(origs)

    for filename in Path("merged_fanfics").glob("*.txt"):
        if filename.name in origs:
            copyfile(filename, TEMP_ORIGS / filename.name)
        else:
            copyfile(filename, TEMP_FANDOMS / filename.name)

    for i, filename in enumerate(sorted(TEMP_ORIGS.glob("*"),
                                        key=getsize, reverse=True)):
        if i >= MAX_FILES:
            remove(filename)
    for i, filename in enumerate(sorted(TEMP_FANDOMS.glob("*"),
                                        key=getsize, reverse=True)):
        if i >= MAX_FILES:
            remove(filename)

    print("making origs archive, please wait...")
    make_archive("origs", "zip", TEMP_ORIGS, ".")
    print("making fandoms archive, please wait...")
    make_archive("fandoms", "zip", TEMP_FANDOMS, ".")
    print("archives made. cleaning up...")
    rmtree(TEMP_DATASET)
    print("cleaned up")


zip_dataset()
