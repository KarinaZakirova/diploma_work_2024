import random
from pathlib import Path
import jsonlines


TEXTS = "pan22-authorship-verification-training.jsonl"
AUTHORS = "pan22-authorship-verification-training-truth.jsonl"

PAIRS_REQUIRED = 100


def randhex(length):
    return "".join(random.choice("0123456789abcdef") for _ in range(length))


def generate_id():
    return "-".join([
        randhex(8),
        randhex(4),
        randhex(4),
        randhex(4),
        randhex(12),
    ])


def list_all_authors():
    authors = set()
    for filename in Path("merged_fanfics", encoding="utf-8").glob("*.txt"):
        authors.add(filename.stem.split("_")[0])
    return authors


def main():
    fanfic_files = list(Path("fanfics", encoding="utf-8").glob("*.txt"))
    random.shuffle(fanfic_files)

    trues = 0
    falses = 0

    while trues <= PAIRS_REQUIRED or falses <= PAIRS_REQUIRED:
        filename_1 = random.choice(fanfic_files)
        filename_2 = random.choice(fanfic_files)

        author_1 = filename_1.stem.split("_")[0]
        author_2 = filename_2.stem.split("_")[0]

        uuid = generate_id()

        with open(filename_1, encoding="utf-8") as f:
            text_1 = f.read().replace("\n", "<nl>")
        with open(filename_2, encoding="utf-8") as f:
            text_2 = f.read().replace("\n", "<nl>")

        if ((author_1 == author_2 and trues > PAIRS_REQUIRED) or
                (author_1 != author_2 and falses > PAIRS_REQUIRED)):
            continue

        trues += author_1 == author_2
        falses += author_1 != author_2

        print(trues, falses)

        with open(TEXTS, "a+", encoding="utf-8") as f:
            jsonlines.Writer(f).write(
                {
                    "id": uuid,
                    "discourse_types": ["email", "text_message"],
                    "pair": [text_1, text_2],
                }
            )

        with open(AUTHORS, "a+", encoding="utf-8") as f:
            jsonlines.Writer(f).write(
                {
                    "id": uuid,
                    "same": author_1 == author_2,
                    "authors": [author_1, author_2],
                }
            )


if __name__ == "__main__":
    main()
