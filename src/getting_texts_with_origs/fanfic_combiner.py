from pathlib import Path
from collections import Counter

def combine_fanfics():
    for filename in Path("fanfics").glob("*.txt"):
        author, fanfic, chapter = filename.stem.split("_")
        with open(filename) as f:
            text = f.read()
        with open(Path("merged_fanfics") / f"{author}_{fanfic}.txt", "a+", encoding="utf-8") as f:
            f.write(text + "\n======================================================\n")

def count_authors():
    long_fanfics = []
    for filename in Path("merged_fanfics").glob("*.txt"):
        author, fanfic = filename.stem.split("_")
        with open(filename) as f:
            wc = len(f.read().split())
        # if wc >= 2500:
        if wc >= 0:
            long_fanfics.append(author)
    print(Counter(long_fanfics))

if __name__ == "__main__":
    combine_fanfics()
    count_authors()
