import random
from pathlib import Path
import jsonlines


TEXTS = "pan22-authorship-verification-training.jsonl"
AUTHORS = "pan22-authorship-verification-training-truth.jsonl"


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
    fanfic_files = list(Path("merged_fanfics", encoding="utf-8").glob("*.txt"))
    random.shuffle(fanfic_files)
    for filename in fanfic_files:

        author, fanfic = filename.stem.split("_")

        with open(filename, encoding="utf-8") as f:
            text = f.read().replace("\n", "<nl>")
        uuid = generate_id()

        with open(TEXTS, "a+", encoding="utf-8") as f:
            jsonlines.Writer(f).write(
                {
                    "id": uuid,
                    "discourse_types": ["email", "text_message"],
                    "pair": [text, text],
                }
            )
        # TODO: заменить на реальный подбор настоящих авторов
        author_placeholder = random.choice([True, False])
        authors = []
        if author_placeholder:
            authors = [author, author]
        else:
            authors = [author, random.choice(list(list_all_authors()
                                                  - set([author])))]
        with open(AUTHORS, "a+", encoding="utf-8") as f:
            jsonlines.Writer(f).write(
                {
                    "id": uuid,
                    "same": author_placeholder,
                    "authors": authors,
                }
            )


if __name__ == "__main__":
    main()